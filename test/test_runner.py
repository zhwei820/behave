from __future__ import with_statement

from collections import defaultdict
import os.path
import sys
import warnings

from mock import Mock, patch
from nose.tools import *

from behave import model, runner
from behave.configuration import ConfigError

class TestContext(object):
    def setUp(self):
        self.context = runner.Context()

    def test_attribute_set_at_upper_level_visible_at_lower_level(self):
        self.context.thing = 'stuff'
        self.context._push()
        eq_(self.context.thing, 'stuff')

    def test_attribute_set_at_lower_level_not_visible_at_upper_level(self):
        self.context._push()
        self.context.thing = 'stuff'
        self.context._pop()
        assert getattr(self.context, 'thing', None) is None

    def test_attributes_set_at_upper_level_visible_at_lower_level(self):
        self.context.thing = 'stuff'
        self.context._push()
        eq_(self.context.thing, 'stuff')
        self.context.other_thing = 'more stuff'
        self.context._push()
        eq_(self.context.thing, 'stuff')
        eq_(self.context.other_thing, 'more stuff')
        self.context.third_thing = 'wombats'
        self.context._push()
        eq_(self.context.thing, 'stuff')
        eq_(self.context.other_thing, 'more stuff')
        eq_(self.context.third_thing, 'wombats')

    def test_attributes_set_at_lower_level_not_visible_at_upper_level(self):
        self.context.thing = 'stuff'
        self.context._push()
        self.context.other_thing = 'more stuff'
        self.context._push()
        self.context.third_thing = 'wombats'
        eq_(self.context.thing, 'stuff')
        eq_(self.context.other_thing, 'more stuff')
        eq_(self.context.third_thing, 'wombats')
        self.context._pop()
        eq_(self.context.thing, 'stuff')
        eq_(self.context.other_thing, 'more stuff')
        assert getattr(self.context, 'third_thing', None) is None
        self.context._pop()
        eq_(self.context.thing, 'stuff')
        assert getattr(self.context, 'other_thing', None) is None
        assert getattr(self.context, 'third_thing', None) is None

    def test_masking_attribute_at_lower_level_causes_warning(self):
        warns = []

        def catch_warning(*args, **kwargs):
            warns.append(args[0])

        old_showwarning = warnings.showwarning
        warnings.showwarning = catch_warning

        self.context.thing = 'stuff'
        self.context._push()
        self.context.thing = 'other stuff'

        warnings.showwarning = old_showwarning

        print repr(warns)
        assert warns
        warning = warns[0]
        assert isinstance(warning, runner.ContextMaskWarning)
        info = warning.args[0]
        assert info.startswith('Step code'), "%r doesn't start with 'Step code'" % info
        assert "'thing'" in info, '%r not in %r' % ("'thing'", info)
        file = __file__.rsplit('.', 1)[0]
        assert file in info, '%r not in %r' % (file, info)

    def test_setting_root_attribute_that_masks_existing_causes_warning(self):
        warns = []

        def catch_warning(*args, **kwargs):
            warns.append(args[0])

        old_showwarning = warnings.showwarning
        warnings.showwarning = catch_warning

        self.context._push()
        self.context.thing = 'teak'
        self.context._set_root_attribute('thing', 'oak')

        warnings.showwarning = old_showwarning

        print repr(warns)
        assert warns
        warning = warns[0]
        assert isinstance(warning, runner.ContextMaskWarning)
        info = warning.args[0]
        assert info.startswith('behave runner'), "%r doesn't start with 'behave runner'" % info
        assert "'thing'" in info, '%r not in %r' % ("'thing'", info)
        file = __file__.rsplit('.', 1)[0]
        assert file in info, '%r not in %r' % (file, info)

class TestStepRegistry(object):
    def test_add_definition_adds_to_lowercased_keyword(self):
        registry = runner.StepRegistry()
        with patch('behave.matchers.get_matcher') as get_matcher:
            func = lambda x: -x
            string = 'just a test string'
            magic_object = object()
            get_matcher.return_value = magic_object

            for step_type in registry.steps.keys():
                mock = Mock()
                registry.steps[step_type] = mock

                registry.add_definition(step_type.upper(), string, func)

                get_matcher.assert_called_with(func, string)
                mock.append.assert_called_with(magic_object)

    def test_find_match_with_specific_step_type_also_searches_generic(self):
        registry = runner.StepRegistry()

        given_mock = Mock()
        given_mock.match.return_value = None
        step_mock = Mock()
        step_mock.match.return_value = None

        registry.steps['given'].append(given_mock)
        registry.steps['step'].append(step_mock)

        step = Mock()
        step.step_type = 'given'
        step.name = 'just a test step'

        assert registry.find_match(step) is None

        given_mock.match.assert_called_with(step.name)
        step_mock.match.assert_called_with(step.name)

    def test_find_match_with_no_match_returns_none(self):
        registry = runner.StepRegistry()

        step_defs = [Mock() for x in range(0, 10)]
        for mock in step_defs:
            mock.match.return_value = None

        registry.steps['when'] = step_defs

        step = Mock()
        step.step_type = 'when'
        step.name = 'just a test step'

        assert registry.find_match(step) is None

    def test_find_match_with_a_match_returns_match(self):
        registry = runner.StepRegistry()

        step_defs = [Mock() for x in range(0, 10)]
        for mock in step_defs:
            mock.match.return_value = None
        magic_object = object()
        step_defs[5].match.return_value = magic_object

        registry.steps['then'] = step_defs

        step = Mock()
        step.step_type = 'then'
        step.name = 'just a test step'

        assert registry.find_match(step) is magic_object
        for mock in step_defs[6:]:
            eq_(mock.match.call_count, 0)


class TestRunner(object):
    def test_load_hooks_execfiles_hook_file(self):
        with patch('behave.runner.exec_file') as ef:
            with patch('os.path.exists') as exists:
                exists.return_value = True
                base_dir = 'fake/path'
                hooks_path = os.path.join(base_dir, 'environment.py')

                r = runner.Runner(None)
                r.base_dir = base_dir
                r.load_hooks()

                exists.assert_called_with(hooks_path)
                ef.assert_called_with(hooks_path, r.hooks)

    def test_make_step_decorator_ends_up_adding_a_step_definition(self):
        r = runner.Runner(None)
        with patch.object(r.steps, 'add_definition') as add_definition:
            step_type = object()
            string = object()
            func = object()

            decorator = r.make_step_decorator(step_type)
            wrapper = decorator(string)
            assert wrapper(func) is func
            add_definition.assert_called_with(step_type, string, func)

    def test_run_hook_runs_a_hook_that_exists(self):
        r = runner.Runner(None)
        r.hooks['before_lunch'] = hook = Mock()
        args = (Mock(),) * 3
        r.run_hook('before_lunch', *args)

        hook.assert_called_with(*args)


class TestRunWithPaths(object):
    def setUp(self):
        self.config = Mock()
        self.runner = runner.Runner(self.config)
        self.load_hooks = self.runner.load_hooks = Mock()
        self.load_step_definitions = self.runner.load_step_definitions = Mock()
        self.run_hook = self.runner.run_hook = Mock()
        self.run_step = self.runner.run_step = Mock()
        self.feature_files = self.runner.feature_files = Mock()
        self.calculate_summaries = self.runner.calculate_summaries = Mock()

        self.parse_file_patch = patch('behave.runner.parser.parse_file')
        self.parse_file = self.parse_file_patch.start()
        self.abspath_patch = patch('os.path.abspath')
        self.abspath = self.abspath_patch.start()
        self.context_class = patch('behave.runner.Context')
        context_class = self.context_class.start()
        context_class.return_value = self.context = Mock()
        self.formatter_class = patch('behave.runner.PrettyFormatter')
        formatter_class = self.formatter_class.start()
        formatter_class.return_value = self.formatter = Mock()

    def tearDown(self):
        self.parse_file_patch.stop()
        self.abspath_patch.stop()
        self.context_class.stop()
        self.formatter_class.stop()

    def test_loads_hooks_and_step_definitions(self):
        self.feature_files.return_value = []
        self.runner.run_with_paths()

        assert self.load_hooks.called
        assert self.load_step_definitions.called

    def test_runs_before_all_and_after_all_hooks(self):
        # Make runner.feature_files() and runner.run_hook() the same mock so
        # we can make sure things happen in the right order.
        self.runner.feature_files = self.run_hook
        self.runner.feature_files.return_value = []
        self.runner.run_with_paths()

        eq_(self.run_hook.call_args_list, [
            (('before_all', self.runner.context), {}),
            ((), {}),
            (('after_all', self.runner.context), {}),
        ])

    def test_parses_feature_files_and_appends_to_feature_list(self):
        feature_files = ['one', 'two', 'three']
        feature = Mock()
        feature.tags = []
        feature.__iter__ = Mock(return_value=iter([]))
        self.runner.feature_files.return_value = feature_files
        self.abspath.side_effect = lambda x: x.upper()
        self.config.lang = 'fritz'
        self.parse_file.return_value = feature

        self.runner.run_with_paths()

        expected_parse_file_args = \
            [((x.upper(),), {'language': 'fritz'}) for x in feature_files]
        eq_(self.parse_file.call_args_list, expected_parse_file_args)
        eq_(self.runner.features, [feature] * 3)

    def test_formatter_sequence_with_no_scenarios_or_background(self):
        feature_files = ['one']
        feature = Mock()
        feature.tags = []
        feature.background = None
        feature.__iter__ = Mock(return_value=iter([]))
        self.runner.feature_files.return_value = feature_files
        self.parse_file.return_value = feature

        self.runner.run_with_paths()

        self.formatter.uri.assert_called_with('one')
        self.formatter.feature.assert_called_with(feature)
        assert not self.formatter.background.called
        self.formatter.eof.assert_called_with()

    def test_formatter_background_called_when_feature_has_background(self):
        feature_files = ['one']
        feature = Mock()
        feature.tags = []
        feature.background = Mock()
        feature.__iter__ = Mock(return_value=iter([]))
        self.runner.feature_files.return_value = feature_files
        self.parse_file.return_value = feature

        self.runner.run_with_paths()

        self.formatter.uri.assert_called_with('one')
        self.formatter.feature.assert_called_with(feature)
        self.formatter.background.assert_called_with(feature.background)
        self.formatter.eof.assert_called_with()

    def test_formatter_scenario_and_step_invoked_correctly(self):
        self.config.stdout_capture = False
        self.config.log_capture = False
        feature_files = ['one']
        feature = Mock()
        feature.tags = []
        feature.background = None
        scenario1 = Mock()
        scenario1.tags = []
        steps1 = [Mock(), Mock()]
        scenario1.__iter__ = Mock(return_value=iter(steps1))
        scenario2 = Mock()
        scenario2.tags = []
        steps2 = [Mock(), Mock(), Mock()]
        scenario2.__iter__ = Mock(return_value=iter(steps2))
        scenarios = [scenario1, scenario2]
        feature.__iter__ = Mock(return_value=iter(scenarios))
        self.runner.feature_files.return_value = feature_files
        self.parse_file.return_value = feature

        self.runner.run_with_paths()

        self.formatter.uri.assert_called_with('one')
        self.formatter.feature.assert_called_with(feature)
        eq_(self.formatter.scenario.call_args_list, [
            ((x,), {}) for x in scenarios
        ])
        eq_(self.formatter.step.call_args_list, [
            ((x,), {}) for x in steps1 + steps2
        ])
        self.formatter.eof.assert_called_with()

    def test_the_whole_hooks_gamut(self):
        # Make runner.feature_files(), runner.run_step() and runner.run_hook()
        # the same mock so we can make sure things happen in the right order.
        self.runner.feature_files = self.run_hook
        self.runner.run_step = self.run_hook

        self.config.stdout_capture = False
        self.config.log_capture = False
        self.config.tags.check.return_value = True
        feature_files = ['one']
        feature = Mock()
        feature.tags = ['feature_tag_one', 'feature_tag_two']
        feature.background = None
        scenario1 = Mock()
        scenario1.tags = ['scenario_tag_one', 'scenario_tag_two']
        steps1 = [Mock(), Mock()]
        scenario1.__iter__ = Mock(side_effect=lambda: iter(steps1))
        scenario2 = Mock()
        scenario2.tags = ['scenario_tag_three']
        steps2 = [Mock(), Mock(), Mock()]
        scenario2.__iter__ = Mock(side_effect=lambda: iter(steps2))
        scenarios = [scenario1, scenario2]
        feature.__iter__ = Mock(return_value=iter(scenarios))
        self.runner.feature_files.return_value = feature_files
        self.parse_file.return_value = feature

        self.runner.run_with_paths()

        context = self.runner.context
        expected_calls = [
            ('before_all', context),
            (), # feature_files
            ('before_tag', context, 'feature_tag_one'),
            ('before_tag', context, 'feature_tag_two'),
            ('before_feature', context, feature),
            ('before_tag', context, 'scenario_tag_one'),
            ('before_tag', context, 'scenario_tag_two'),
            ('before_scenario', context, scenario1),
            (steps1[0],), # run_step
            (steps1[1],), # run_step
            ('after_scenario', context, scenario1),
            ('after_tag', context, 'scenario_tag_one'),
            ('after_tag', context, 'scenario_tag_two'),
            ('before_tag', context, 'scenario_tag_three'),
            ('before_scenario', context, scenario2),
            (steps2[0],), # run_step
            (steps2[1],), # run_step
            (steps2[2],), # run_step
            ('after_scenario', context, scenario2),
            ('after_tag', context, 'scenario_tag_three'),
            ('after_feature', context, feature),
            ('after_tag', context, 'feature_tag_one'),
            ('after_tag', context, 'feature_tag_two'),
            ('after_all', context),
        ]
        eq_(self.run_hook.call_args_list, [(x, {}) for x in expected_calls])

    def test_feature_hooks_not_run_if_feature_not_being_run(self):
        self.config.stdout_capture = False
        self.config.log_capture = False
        self.config.tags.check.return_value = False

        feature_files = ['one']
        feature = Mock()
        feature.tags = ['feature_tag_one', 'feature_tag_two']
        feature.background = None
        feature.__iter__ = Mock(return_value=iter([]))

        self.runner.feature_files.return_value = feature_files
        self.parse_file.return_value = feature

        self.runner.run_with_paths()

        eq_(self.run_hook.call_args_list, [
            (('before_all', self.runner.context), {}),
            (('after_all', self.runner.context), {}),
        ])

    def test_scenario_hooks_not_run_if_scenario_not_being_run(self):
        self.config.stdout_capture = False
        self.config.log_capture = False

        def tags1(*args, **kwargs):
            def tags2(*args, **kwargs):
                return False
            self.config.tags.check.side_effect = tags2
            return True
        self.config.tags.check.side_effect = tags1

        feature_files = ['one']
        feature = Mock()
        feature.tags = ['feature_tag_one']
        feature.background = None
        scenario = Mock()
        scenario.tags = ['scenario_tag_one']
        steps = [Mock(), Mock()]
        scenario.__iter__ = Mock(return_value=iter(steps))
        feature.__iter__ = Mock(return_value=iter([scenario]))

        self.runner.feature_files.return_value = feature_files
        self.parse_file.return_value = feature

        self.runner.run_with_paths()

        eq_(self.run_hook.call_args_list, [
            (('before_all', self.runner.context), {}),
            (('before_tag', self.runner.context, 'feature_tag_one'), {}),
            (('before_feature', self.runner.context, feature), {}),
            (('after_feature', self.runner.context, feature), {}),
            (('after_tag', self.runner.context, 'feature_tag_one'), {}),
            (('after_all', self.runner.context), {}),
        ])

    if sys.version_info[0] == 3:
        stringio_target = 'io.StringIO'
    else:
        stringio_target = 'StringIO.StringIO'

    @patch(stringio_target)
    @patch('behave.runner.MemoryHandler')
    def test_handles_stdout_and_logs(self, handler_class, stringio):
        self.config.stdout_capture = True
        self.config.log_capture = True
        self.config.tags.check.return_value = True

        feature_files = ['one']
        feature = Mock()
        feature.tags = ['feature_tag_one']
        feature.background = None
        scenario = Mock()
        scenario.tags = ['scenario_tag_one']
        steps = [Mock(), Mock()]
        scenario.__iter__ = Mock(return_value=iter(steps))
        feature.__iter__ = Mock(return_value=iter([scenario]))

        self.runner.feature_files.return_value = feature_files
        self.parse_file.return_value = feature

        stringio.return_value = Mock()
        handler_class.return_value = handler = Mock()

        self.runner.run_with_paths()

        assert stringio.called
        assert self.runner.stdout_capture is stringio.return_value

        handler_class.assert_called_with(self.config)
        handler.inveigle.assert_called_with()
        handler.abandon.assert_called_with()

    def test_skipped_steps_set_status_correctly(self):
        self.config.stdout_capture = False
        self.config.log_capture = False

        def tags1(*args, **kwargs):
            def tags2(*args, **kwargs):
                return False
            self.config.tags.check.side_effect = tags2
            return True
        self.config.tags.check.side_effect = tags1

        feature_files = ['one']
        feature = Mock()
        feature.tags = ['feature_tag_one', 'feature_tag_two']
        feature.background = None
        scenario1 = Mock()
        scenario1.status = None
        scenario1.tags = ['scenario_tag_one', 'scenario_tag_two']
        steps1 = [Mock(), Mock()]
        scenario1.__iter__ = Mock(side_effect=lambda: iter(steps1))
        scenario2 = Mock()
        scenario2.status = 'stoned'
        scenario2.tags = ['scenario_tag_three']
        steps2 = [Mock(), Mock(), Mock()]
        scenario2.__iter__ = Mock(side_effect=lambda: iter(steps2))
        scenarios = [scenario1, scenario2]
        feature.__iter__ = Mock(return_value=iter(scenarios))
        self.runner.feature_files.return_value = feature_files
        self.parse_file.return_value = feature

        self.runner.run_with_paths()

        assert False not in [s.status == 'skipped' for s in steps1 + steps2]
        eq_(scenario1.status, 'skipped')
        eq_(scenario2.status, 'stoned')

    def test_failed_step_causes_remaining_steps_to_be_skipped(self):
        self.config.stdout_capture = False
        self.config.log_capture = False
        self.config.tags.check.return_value = True

        feature_files = ['one']
        feature = Mock()
        feature.tags = ['feature_tag_one']
        feature.background = None
        scenario = Mock()
        scenario.tags = ['scenario_tag_one']
        steps = [Mock(), Mock()]
        scenario.__iter__ = Mock(side_effect=lambda: iter(steps))
        feature.__iter__ = Mock(return_value=iter([scenario]))

        self.runner.feature_files.return_value = feature_files
        self.parse_file.return_value = feature
        self.run_step.return_value = False

        assert self.runner.run_with_paths()

        eq_(steps[1].status, 'skipped')

    def test_failed_step_causes_context_failure_to_be_set(self):
        self.config.stdout_capture = False
        self.config.log_capture = False
        self.config.tags.check.return_value = True

        feature_files = ['one']
        feature = Mock()
        feature.tags = ['feature_tag_one']
        feature.background = None
        scenario = Mock()
        scenario.tags = ['scenario_tag_one']
        steps = [Mock(), Mock()]
        scenario.__iter__ = Mock(side_effect=lambda: iter(steps))
        feature.__iter__ = Mock(return_value=iter([scenario]))

        self.runner.feature_files.return_value = feature_files
        self.parse_file.return_value = feature
        self.run_step.return_value = False

        assert self.runner.run_with_paths()

        self.context._set_root_attribute.assert_called_with('failed', True)


def raiser(exception):
    def func(*args, **kwargs):
        raise exception
    return func


class TestRunStep(object):
    def setUp(self):
        self.config = Mock()
        self.runner = runner.Runner(self.config)
        self.context = self.runner.context = Mock()
        self.formatter = self.runner.formatter = Mock()
        self.steps = self.runner.steps = Mock()
        self.stdout_capture = self.runner.stdout_capture = Mock()
        self.stdout_capture.getvalue.return_value = ''
        self.log_capture = self.runner.log_capture = Mock()
        self.log_capture.getvalue.return_value = ''
        self.run_hook = self.runner.run_hook = Mock()

    def test_run_step_resets_text_and_table_before_step(self):
        self.steps.find_match.return_value = None
        assert not self.runner.run_step(Mock())

        call_args_list = self.context._set_root_attribute.call_args_list
        call_args_list = [x[0] for x in call_args_list]
        assert ('text', None) in call_args_list
        assert ('table', None) in call_args_list

    def test_run_step_appends_step_to_undefined_when_no_match_found(self):
        step = Mock()
        self.steps.find_match.return_value = None
        assert not self.runner.run_step(step)

        assert step in self.runner.undefined
        eq_(step.status, 'undefined')

    def test_run_step_reports_undefined_step_via_formatter_when_not_quiet(self):
        step = Mock()
        self.steps.find_match.return_value = None
        assert not self.runner.run_step(step)

        self.formatter.match.assert_called_with(model.NoMatch())
        self.formatter.result.assert_called_with(step)

    def test_run_step_with_no_match_does_not_touch_formatter_when_quiet(self):
        step = Mock()
        self.steps.find_match.return_value = None
        assert not self.runner.run_step(step, quiet=True)

        assert not self.formatter.match.called
        assert not self.formatter.result.called

    def test_run_step_when_not_quiet_reports_match_and_result(self):
        step = Mock()
        match = Mock()
        self.steps.find_match.return_value = match

        side_effects = (None, raiser(AssertionError('whee')),
                        raiser(Exception('whee')))
        for side_effect in side_effects:
            match.run.side_effect = side_effect
            self.runner.run_step(step)
            self.formatter.match.assert_called_with(match)
            self.formatter.result.assert_called_with(step)

    def test_run_step_when_quiet_reports_nothing(self):
        step = Mock()
        match = Mock()
        self.steps.find_match.return_value = match

        side_effects = (None, raiser(AssertionError('whee')),
                raiser(Exception('whee')))
        for side_effect in side_effects:
            match.run.side_effect = side_effect
            self.runner.run_step(step, quiet=True)
            assert not self.formatter.match.called
            assert not self.formatter.result.called

    def test_run_step_runs_before_hook_then_match_then_after_hook(self):
        step = Mock()
        match = Mock()
        self.steps.find_match.return_value = match

        side_effects = (None, AssertionError('whee'), Exception('whee'))
        for side_effect in side_effects:
            # Make match.run() and runner.run_hook() the same mock so
            # we can make sure things happen in the right order.
            self.runner.run_hook = match.run = Mock()

            def effect(thing):
                def raiser(*args, **kwargs):
                    match.run.side_effect = None
                    if thing:
                        raise thing

                def nonraiser(*args, **kwargs):
                    match.run.side_effect = raiser

                return nonraiser

            match.run.side_effect = effect(side_effect)
            self.runner.run_step(step)

            eq_(match.run.call_args_list, [
                (('before_step', self.context, step), {}),
                ((self.context,), {}),
                (('after_step', self.context, step), {}),
            ])

    def test_run_step_sets_table_if_present(self):
        step = Mock()
        step.table = Mock()
        step.text = None
        self.steps.find_match.return_value = Mock()

        self.runner.run_step(step)

        self.context._set_root_attribute.assert_called_with('table', step.table)

    def test_run_step_sets_text_if_present(self):
        step = Mock()
        step.table = None
        step.text = Mock()
        self.steps.find_match.return_value = Mock()

        self.runner.run_step(step)

        self.context._set_root_attribute.assert_called_with('text', step.text)

    def test_run_step_sets_status_to_passed_if_nothing_goes_wrong(self):
        step = Mock()
        step.error_message = None
        self.steps.find_match.return_value = Mock()

        self.runner.run_step(step)

        eq_(step.status, 'passed')
        eq_(step.error_message, None)

    def test_run_step_sets_status_to_failed_on_assertion_error(self):
        step = Mock()
        step.error_message = None
        match = Mock()
        match.run.side_effect = raiser(AssertionError('whee'))
        self.steps.find_match.return_value = match

        self.runner.run_step(step)

        eq_(step.status, 'failed')
        assert step.error_message.startswith('Assertion Failed')

    @patch('traceback.format_exc')
    def test_run_step_sets_status_to_failed_on_exception(self, format_exc):
        step = Mock()
        step.error_message = None
        match = Mock()
        match.run.side_effect = raiser(Exception('whee'))
        self.steps.find_match.return_value = match
        format_exc.return_value = 'something to do with an exception'

        self.runner.run_step(step)

        eq_(step.status, 'failed')
        eq_(step.error_message, format_exc.return_value)

    @patch('time.time')
    def test_run_step_calculates_duration(self, time_time):
        step = Mock()
        step.duration = None
        match = Mock()
        self.steps.find_match.return_value = match

        def time_time_1():
            def time_time_2():
                return 23
            time_time.side_effect = time_time_2
            return 17

        side_effects = (None, raiser(AssertionError('whee')),
                raiser(Exception('whee')))
        for side_effect in side_effects:
            match.run.side_effect = side_effect
            time_time.side_effect = time_time_1

            self.runner.run_step(step)
            eq_(step.duration, 23 - 17)

    def test_run_step_captures_stdout_if_requested(self):
        step = Mock()
        match = Mock()
        self.steps.find_match.return_value = match

        def printer(*args, **kwargs):
            print 'carrots'

        match.run.side_effect = printer

        assert self.runner.run_step(step)

        call_args_list = self.stdout_capture.write.call_args_list
        stdout = ''.join(a[0][0] for a in call_args_list)
        eq_(stdout.strip(), 'carrots')

    def test_run_step_does_not_capture_stdout_if_requested(self):
        step = Mock()
        match = Mock()
        self.steps.find_match.return_value = match
        self.config.stdout_capture = False

        def printer(*args, **kwargs):
            print 'carrots'

        match.run.side_effect = printer

        assert self.runner.run_step(step)

        assert not self.stdout_capture.write.called

    def test_run_step_appends_any_captured_stdout_on_failure(self):
        step = Mock()
        match = Mock()
        self.steps.find_match.return_value = match
        self.stdout_capture.getvalue.return_value = 'frogs'
        match.run.side_effect = raiser(Exception('halibut'))

        assert not self.runner.run_step(step)

        assert 'Captured stdout:' in step.error_message
        assert 'frogs' in step.error_message

    def test_run_step_appends_any_captured_logging_on_failure(self):
        step = Mock()
        match = Mock()
        self.steps.find_match.return_value = match
        self.log_capture.getvalue.return_value = 'toads'
        match.run.side_effect = raiser(AssertionError('kipper'))

        assert not self.runner.run_step(step)

        assert 'Captured logging:' in step.error_message
        assert 'toads' in step.error_message


class FsMock(object):
    def __init__(self, *paths):
        self.base = os.path.abspath('.')
        paths = [os.path.join(self.base, path) for path in paths]
        self.paths = paths
        self.files = set()
        self.dirs = defaultdict(list)
        for path in paths:
            if path[-1] == '/':
                self.dirs[path[:-1]] = []
                d, p = os.path.split(path[:-1])
                while d and p:
                    self.dirs[d].append(p)
                    d, p = os.path.split(d)
            else:
                self.files.add(path)
                d, f = os.path.split(path)
                self.dirs[d].append(f)
        self.calls = []
    def listdir(self, dir):
        self.calls.append(('listdir', dir))
        return self.dirs.get(dir, [])
    def isfile(self, path):
        self.calls.append(('isfile', path))
        return path in self.files
    def isdir(self, path):
        self.calls.append(('isdir', path))
        return path in self.dirs
    def exists(self, path):
        self.calls.append(('exists', path))
        return path in self.dirs or path in self.files
    def walk(self, path, l=None):
        if l is None:
            assert path in self.dirs, '%s not in %s' % (path, self.dirs)
            l = []
        dirnames = []
        filenames = []
        for e in self.dirs[path]:
            if os.path.join(path, e) in self.dirs:
                dirnames.append(e)
                self.walk(os.path.join(path, e), l)
            else:
                filenames.append(e)
        l.append((path, dirnames, filenames))
        return l

    # utilities that we need
    def dirname(self, path, orig=os.path.dirname):
        return orig(path)
    def abspath(self, path, orig=os.path.abspath):
        return orig(path)
    def join(self, a, b, orig=os.path.join):
        return orig(a, b)



class TestFeatureDirectory(object):
    def test_default_path_no_steps(self):
        config = Mock()
        config.paths = []
        config.verbose = True
        r = runner.Runner(config)

        fs = FsMock()

        # will look for a "features" directory and not find one
        with patch('os.path', fs):
            assert_raises(ConfigError, r.setup_paths)

        ok_(('isdir', os.path.join(fs.base, 'features/steps')) in fs.calls)

    def test_default_path_no_features(self):
        config = Mock()
        config.paths = []
        config.verbose = True
        r = runner.Runner(config)

        fs = FsMock('features/steps/')
        with patch('os.path', fs):
            with patch('os.walk', fs.walk):
                assert_raises(ConfigError, r.setup_paths)

    def test_default_path(self):
        config = Mock()
        config.paths = []
        config.verbose = True
        r = runner.Runner(config)

        fs = FsMock('features/steps/', 'features/foo.feature')

        with patch('os.path', fs):
            with patch('os.walk', fs.walk):
                with r.path_manager:
                    r.setup_paths()

        eq_(r.base_dir, os.path.abspath('features'))

    def test_supplied_feature_file(self):
        config = Mock()
        config.paths = ['foo.feature']
        config.verbose = True
        r = runner.Runner(config)

        fs = FsMock('steps/', 'foo.feature')

        with patch('os.path', fs):
            with patch('os.walk', fs.walk):
                with r.path_manager:
                    r.setup_paths()
        ok_(('isdir', os.path.join(fs.base, 'steps')) in fs.calls)
        ok_(('isfile', os.path.join(fs.base, 'foo.feature')) in fs.calls)

        eq_(r.base_dir, fs.base)

    def test_supplied_feature_file_no_steps(self):
        config = Mock()
        config.paths = ['foo.feature']
        config.verbose = True
        r = runner.Runner(config)

        fs = FsMock('foo.feature')

        with patch('os.path', fs):
            with patch('os.walk', fs.walk):
                with r.path_manager:
                    assert_raises(ConfigError, r.setup_paths)

    def test_supplied_feature_directory(self):
        config = Mock()
        config.paths = ['spam']
        config.verbose = True
        r = runner.Runner(config)

        fs = FsMock('spam/', 'spam/steps/', 'spam/foo.feature')

        with patch('os.path', fs):
            with patch('os.walk', fs.walk):
                with r.path_manager:
                    r.setup_paths()

        ok_(('isdir', os.path.join(fs.base, 'spam', 'steps')) in fs.calls)

        eq_(r.base_dir, os.path.join(fs.base, 'spam'))

    def test_supplied_feature_directory_no_steps(self):
        config = Mock()
        config.paths = ['spam']
        config.verbose = True
        r = runner.Runner(config)

        fs = FsMock('spam/', 'spam/foo.feature')

        with patch('os.path', fs):
            with patch('os.walk', fs.walk):
                assert_raises(ConfigError, r.setup_paths)

        ok_(('isdir', os.path.join(fs.base, 'spam', 'steps')) in fs.calls)

    def test_supplied_feature_directory_missing(self):
        config = Mock()
        config.paths = ['spam']
        config.verbose = True
        r = runner.Runner(config)

        fs = FsMock()

        with patch('os.path', fs):
            with patch('os.walk', fs.walk):
                assert_raises(ConfigError, r.setup_paths)


