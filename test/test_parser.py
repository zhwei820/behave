from nose.tools import *

from behave import model, parser

class Common(object):
    def compare_steps(self, steps, expected):
        have = [(s.step_type, s.keyword, s.name, s.string, s.table) for s in steps]
        eq_(have, expected)

class TestParser(Common):
    def test_parses_feature_name(self):
        feature = parser.parse_feature(u"Feature: Stuff\n")
        eq_(feature.name, "Stuff")

    def test_parses_feature_name_without_newline(self):
        feature = parser.parse_feature(u"Feature: Stuff")
        eq_(feature.name, "Stuff")

    def test_parses_feature_description(self):
        doc = u"""
Feature: Stuff
  In order to thing
  As an entity
  I want to do stuff
""".strip()
        feature = parser.parse_feature(doc)
        eq_(feature.name, "Stuff")
        eq_(feature.description,
            ["In order to thing", "As an entity", "I want to do stuff"])

    def test_parses_feature_with_a_tag(self):
        doc = u"""
@foo
Feature: Stuff
  In order to thing
  As an entity
  I want to do stuff
""".strip()
        feature = parser.parse_feature(doc)
        eq_(feature.name, "Stuff")
        eq_(feature.description,
            ["In order to thing", "As an entity", "I want to do stuff"])
        eq_(feature.tags, [model.Tag(u'foo', 1)])

    def test_parses_feature_with_more_tags(self):
        doc = u"""
@foo @bar @baz @qux @winkle_pickers @number8
Feature: Stuff
  In order to thing
  As an entity
  I want to do stuff
""".strip()
        feature = parser.parse_feature(doc)
        eq_(feature.name, "Stuff")
        eq_(feature.description,
            ["In order to thing", "As an entity", "I want to do stuff"])
        eq_(feature.tags, [model.Tag(name, 1)
            for name in (u'foo', u'bar', u'baz', u'qux', u'winkle_pickers', u'number8')])

    def test_parses_feature_with_background(self):
        doc = u"""
Feature: Stuff
  Background:
    Given there is stuff
    When I do stuff
    Then stuff happens
""".lstrip()
        feature = parser.parse_feature(doc)
        eq_(feature.name, "Stuff")
        assert(feature.background)
        self.compare_steps(feature.background.steps, [
            ('given', 'Given', 'there is stuff', None, None),
            ('when', 'When', 'I do stuff', None, None),
            ('then', 'Then', 'stuff happens', None, None),
        ])

    def test_parses_feature_with_description_and_background(self):
        doc = u"""
Feature: Stuff
  This... is... STUFF!

  Background:
    Given there is stuff
    When I do stuff
    Then stuff happens
""".lstrip()
        feature = parser.parse_feature(doc)
        eq_(feature.name, "Stuff")
        eq_(feature.description, ["This... is... STUFF!"])
        assert(feature.background)
        self.compare_steps(feature.background.steps, [
            ('given', 'Given', 'there is stuff', None, None),
            ('when', 'When', 'I do stuff', None, None),
            ('then', 'Then', 'stuff happens', None, None),
        ])

    def test_parses_feature_with_a_scenario(self):
        doc = u"""
Feature: Stuff

  Scenario: Doing stuff
    Given there is stuff
    When I do stuff
    Then stuff happens
""".lstrip()
        feature = parser.parse_feature(doc)
        eq_(feature.name, "Stuff")
        assert(len(feature.scenarios) == 1)
        eq_(feature.scenarios[0].name, 'Doing stuff')
        self.compare_steps(feature.scenarios[0].steps, [
            ('given', 'Given', 'there is stuff', None, None),
            ('when', 'When', 'I do stuff', None, None),
            ('then', 'Then', 'stuff happens', None, None),
        ])

    def test_parses_feature_with_description_and_background_and_scenario(self):
        doc = u"""
Feature: Stuff
  Oh my god, it's full of stuff...

  Background:
    Given I found some stuff

  Scenario: Doing stuff
    Given there is stuff
    When I do stuff
    Then stuff happens
""".lstrip()
        feature = parser.parse_feature(doc)
        eq_(feature.name, "Stuff")
        eq_(feature.description, ["Oh my god, it's full of stuff..."])
        assert(feature.background)
        self.compare_steps(feature.background.steps, [
            ('given', 'Given', 'I found some stuff', None, None),
        ])

        assert(len(feature.scenarios) == 1)
        eq_(feature.scenarios[0].name, 'Doing stuff')
        self.compare_steps(feature.scenarios[0].steps, [
            ('given', 'Given', 'there is stuff', None, None),
            ('when', 'When', 'I do stuff', None, None),
            ('then', 'Then', 'stuff happens', None, None),
        ])

    def test_parses_feature_with_multiple_scenarios(self):
        doc = u"""
Feature: Stuff

  Scenario: Doing stuff
    Given there is stuff
    When I do stuff
    Then stuff happens

  Scenario: Doing other stuff
    When stuff happens
    Then I am stuffed

  Scenario: Doing different stuff
    Given stuff
    Then who gives a stuff
""".lstrip()
        feature = parser.parse_feature(doc)
        eq_(feature.name, "Stuff")

        assert(len(feature.scenarios) == 3)

        eq_(feature.scenarios[0].name, 'Doing stuff')
        self.compare_steps(feature.scenarios[0].steps, [
            ('given', 'Given', 'there is stuff', None, None),
            ('when', 'When', 'I do stuff', None, None),
            ('then', 'Then', 'stuff happens', None, None),
        ])

        eq_(feature.scenarios[1].name, 'Doing other stuff')
        self.compare_steps(feature.scenarios[1].steps, [
            ('when', 'When', 'stuff happens', None, None),
            ('then', 'Then', 'I am stuffed', None, None),
        ])

        eq_(feature.scenarios[2].name, 'Doing different stuff')
        self.compare_steps(feature.scenarios[2].steps, [
            ('given', 'Given', 'stuff', None, None),
            ('then', 'Then', 'who gives a stuff', None, None),
        ])

    def test_parses_feature_with_multiple_scenarios_with_tags(self):
        doc = u"""
Feature: Stuff

  Scenario: Doing stuff
    Given there is stuff
    When I do stuff
    Then stuff happens

  @one_tag
  Scenario: Doing other stuff
    When stuff happens
    Then I am stuffed

  @lots @of @tags
  Scenario: Doing different stuff
    Given stuff
    Then who gives a stuff
""".lstrip()
        feature = parser.parse_feature(doc)
        eq_(feature.name, "Stuff")

        assert(len(feature.scenarios) == 3)

        eq_(feature.scenarios[0].name, 'Doing stuff')
        self.compare_steps(feature.scenarios[0].steps, [
            ('given', 'Given', 'there is stuff', None, None),
            ('when', 'When', 'I do stuff', None, None),
            ('then', 'Then', 'stuff happens', None, None),
        ])

        eq_(feature.scenarios[1].name, 'Doing other stuff')
        eq_(feature.scenarios[1].tags, [model.Tag(u'one_tag', 1)])
        self.compare_steps(feature.scenarios[1].steps, [
            ('when', 'When', 'stuff happens', None, None),
            ('then', 'Then', 'I am stuffed', None, None),
        ])

        eq_(feature.scenarios[2].name, 'Doing different stuff')
        eq_(feature.scenarios[2].tags, [model.Tag(n, 1) for n in (u'lots', u'of', u'tags')])
        self.compare_steps(feature.scenarios[2].steps, [
            ('given', 'Given', 'stuff', None, None),
            ('then', 'Then', 'who gives a stuff', None, None),
        ])

    def test_parses_feature_with_multiple_scenarios_and_other_bits(self):
        doc = u"""
Feature: Stuff
  Stuffing

  Background:
    Given you're all stuffed

  Scenario: Doing stuff
    Given there is stuff
    When I do stuff
    Then stuff happens

  Scenario: Doing other stuff
    When stuff happens
    Then I am stuffed

  Scenario: Doing different stuff
    Given stuff
    Then who gives a stuff
""".lstrip()
        feature = parser.parse_feature(doc)
        eq_(feature.name, "Stuff")
        eq_(feature.description, ["Stuffing"])

        assert(feature.background)
        self.compare_steps(feature.background.steps, [
            ('given', 'Given', "you're all stuffed", None, None)
        ])

        assert(len(feature.scenarios) == 3)

        eq_(feature.scenarios[0].name, 'Doing stuff')
        self.compare_steps(feature.scenarios[0].steps, [
            ('given', 'Given', 'there is stuff', None, None),
            ('when', 'When', 'I do stuff', None, None),
            ('then', 'Then', 'stuff happens', None, None),
        ])

        eq_(feature.scenarios[1].name, 'Doing other stuff')
        self.compare_steps(feature.scenarios[1].steps, [
            ('when', 'When', 'stuff happens', None, None),
            ('then', 'Then', 'I am stuffed', None, None),
        ])

        eq_(feature.scenarios[2].name, 'Doing different stuff')
        self.compare_steps(feature.scenarios[2].steps, [
            ('given', 'Given', 'stuff', None, None),
            ('then', 'Then', 'who gives a stuff', None, None),
        ])

    def test_parses_feature_with_a_scenario_with_and_and_but(self):
        doc = u"""
Feature: Stuff

  Scenario: Doing stuff
    Given there is stuff
    And some other stuff
    When I do stuff
    Then stuff happens
    But not the bad stuff
""".lstrip()
        feature = parser.parse_feature(doc)
        eq_(feature.name, "Stuff")
        assert(len(feature.scenarios) == 1)
        eq_(feature.scenarios[0].name, 'Doing stuff')
        self.compare_steps(feature.scenarios[0].steps, [
            ('given', 'Given', 'there is stuff', None, None),
            ('given', 'And', 'some other stuff', None, None),
            ('when', 'When', 'I do stuff', None, None),
            ('then', 'Then', 'stuff happens', None, None),
            ('then', 'But', 'not the bad stuff', None, None),
        ])

    def test_parses_feature_with_a_step_with_a_string_argument(self):
        doc = u'''
Feature: Stuff

  Scenario: Doing stuff
    Given there is stuff:
      """
      So
      Much
      Stuff
      """
    Then stuff happens
'''.lstrip()
        feature = parser.parse_feature(doc)
        eq_(feature.name, "Stuff")
        assert(len(feature.scenarios) == 1)
        eq_(feature.scenarios[0].name, 'Doing stuff')
        self.compare_steps(feature.scenarios[0].steps, [
            ('given', 'Given', 'there is stuff', "So\nMuch\nStuff", None),
            ('then', 'Then', 'stuff happens', None, None),
        ])

    def test_parses_string_argument_correctly_handle_whitespace(self):
        doc = u'''
Feature: Stuff

  Scenario: Doing stuff
    Given there is stuff:
      """
      So
        Much
          Stuff
        Has
      Indents
      """
    Then stuff happens
'''.lstrip()
        feature = parser.parse_feature(doc)
        eq_(feature.name, "Stuff")
        assert(len(feature.scenarios) == 1)
        eq_(feature.scenarios[0].name, 'Doing stuff')
        string = "So\n  Much\n    Stuff\n  Has\nIndents"
        self.compare_steps(feature.scenarios[0].steps, [
            ('given', 'Given', 'there is stuff', string, None),
            ('then', 'Then', 'stuff happens', None, None),
        ])

    def test_parses_feature_with_a_step_with_a_table_argument(self):
        doc = u'''
Feature: Stuff

  Scenario: Doing stuff
    Given we classify stuff:
      | type of stuff | awesomeness | ridiculousness |
      | fluffy        | large       | frequent       |
      | lint          | low         | high           |
      | green         | variable    | awkward        |
    Then stuff is in buckets
'''.lstrip()
        feature = parser.parse_feature(doc)
        eq_(feature.name, "Stuff")
        assert(len(feature.scenarios) == 1)
        eq_(feature.scenarios[0].name, 'Doing stuff')
        table = model.Table(
            ['type of stuff', 'awesomeness', 'ridiculousness'],
            [
                ['fluffy', 'large', 'frequent'],
                ['lint', 'low', 'high'],
                ['green', 'variable', 'awkward'],
            ]
        )
        self.compare_steps(feature.scenarios[0].steps, [
            ('given', 'Given', 'we classify stuff', None, table),
            ('then', 'Then', 'stuff is in buckets', None, None),
        ])

    def test_parses_feature_with_a_scenario_outline(self):
        doc = u'''
Feature: Stuff

  Scenario Outline: Doing all sorts of stuff
    Given we have <Stuff>
    When we do stuff
    Then we have <Things>

    Examples: Some stuff
      | Stuff      | Things   |
      | wool       | felt     |
      | cotton     | thread   |
      | wood       | paper    |
      | explosives | hilarity |
'''.lstrip()
        feature = parser.parse_feature(doc)
        eq_(feature.name, "Stuff")

        assert(len(feature.scenarios) == 1)
        eq_(feature.scenarios[0].name, 'Doing all sorts of stuff')

        table = model.Table(
            ['Stuff', 'Things'],
            [
                ['wool', 'felt'],
                ['cotton', 'thread'],
                ['wood', 'paper'],
                ['explosives', 'hilarity'],
            ]
        )
        eq_(feature.scenarios[0].examples[0].name, 'Some stuff')
        eq_(feature.scenarios[0].examples[0].table, table)
        self.compare_steps(feature.scenarios[0].steps, [
            ('given', 'Given', 'we have <Stuff>', None, None),
            ('when', 'When', 'we do stuff', None, None),
            ('then', 'Then', 'we have <Things>', None, None),
        ])

    def test_parses_feature_with_a_scenario_outline_with_multiple_examples(self):
        doc = u'''
Feature: Stuff

  Scenario Outline: Doing all sorts of stuff
    Given we have <Stuff>
    When we do stuff
    Then we have <Things>

    Examples: Some stuff
      | Stuff      | Things   |
      | wool       | felt     |
      | cotton     | thread   |

    Examples: Some other stuff
      | Stuff      | Things   |
      | wood       | paper    |
      | explosives | hilarity |
'''.lstrip()
        feature = parser.parse_feature(doc)
        eq_(feature.name, "Stuff")

        assert(len(feature.scenarios) == 1)
        eq_(feature.scenarios[0].name, 'Doing all sorts of stuff')
        self.compare_steps(feature.scenarios[0].steps, [
            ('given', 'Given', 'we have <Stuff>', None, None),
            ('when', 'When', 'we do stuff', None, None),
            ('then', 'Then', 'we have <Things>', None, None),
        ])

        table = model.Table(
            ['Stuff', 'Things'],
            [
                ['wool', 'felt'],
                ['cotton', 'thread'],
            ]
        )
        eq_(feature.scenarios[0].examples[0].name, 'Some stuff')
        eq_(feature.scenarios[0].examples[0].table, table)

        table = model.Table(
            ['Stuff', 'Things'],
            [
                ['wood', 'paper'],
                ['explosives', 'hilarity'],
            ]
        )
        eq_(feature.scenarios[0].examples[1].name, 'Some other stuff')
        eq_(feature.scenarios[0].examples[1].table, table)

    def test_parses_feature_with_a_scenario_outline_with_tags(self):
        doc = u'''
Feature: Stuff

  @stuff @derp
  Scenario Outline: Doing all sorts of stuff
    Given we have <Stuff>
    When we do stuff
    Then we have <Things>

    Examples: Some stuff
      | Stuff      | Things   |
      | wool       | felt     |
      | cotton     | thread   |
      | wood       | paper    |
      | explosives | hilarity |
'''.lstrip()
        feature = parser.parse_feature(doc)
        eq_(feature.name, "Stuff")

        assert(len(feature.scenarios) == 1)
        eq_(feature.scenarios[0].name, 'Doing all sorts of stuff')
        eq_(feature.scenarios[0].tags, [model.Tag(u'stuff', 1), model.Tag(u'derp', 1)])
        self.compare_steps(feature.scenarios[0].steps, [
            ('given', 'Given', 'we have <Stuff>', None, None),
            ('when', 'When', 'we do stuff', None, None),
            ('then', 'Then', 'we have <Things>', None, None),
        ])

        table = model.Table(
            ['Stuff', 'Things'],
            [
                ['wool', 'felt'],
                ['cotton', 'thread'],
                ['wood', 'paper'],
                ['explosives', 'hilarity'],
            ]
        )
        eq_(feature.scenarios[0].examples[0].name, 'Some stuff')
        eq_(feature.scenarios[0].examples[0].table, table)

    def test_parses_feature_with_the_lot(self):
        doc = u'''
@derp
Feature: Stuff
  In order to test my parser
  As a test runner
  I want to run tests

  Background:
    Given this is a test

  @fred
  Scenario: Testing stuff
    Given we are testing
    And this is only a test
    But this is an important test
    When we test with a multiline string:
      """
      Yarr, my hovercraft be full of stuff.
      Also, I be feelin' this pirate schtick be a mite overdone, me hearties.
          Also: rum.
      """
    Then we want it to work

  Scenario Outline: Gosh this is long
    Given this is <length>
    Then we want it to be <width>
    But not <height>

    Examples: Initial
      | length | width | height |
      | 1      | 2     | 3      |
      | 4      | 5     | 6      |

    Examples: Subsequent
      | length | width | height |
      | 7      | 8     | 9      |

  Scenario: This one doesn't have a tag
    Given we don't have a tag
    Then we don't really mind

  @stuff @derp
  Scenario Outline: Doing all sorts of stuff
    Given we have <Stuff>
    When we do stuff with a table:
      | a | b | c | d | e |
      | 1 | 2 | 3 | 4 | 5 |
      | 6 | 7 | 8 | 9 | 10 |
    Then we have <Things>

    Examples: Some stuff
      | Stuff      | Things   |
      | wool       | felt     |
      | cotton     | thread   |
      | wood       | paper    |
      | explosives | hilarity |
'''.lstrip()
        feature = parser.parse_feature(doc)
        eq_(feature.name, "Stuff")
        eq_(feature.tags, [model.Tag(u'derp', 1)])
        eq_(feature.description, ['In order to test my parser',
                                  'As a test runner', 'I want to run tests'])

        assert(feature.background)
        self.compare_steps(feature.background.steps, [
            ('given', 'Given', 'this is a test', None, None)
        ])

        assert(len(feature.scenarios) == 4)

        eq_(feature.scenarios[0].name, 'Testing stuff')
        eq_(feature.scenarios[0].tags, [model.Tag(u'fred', 1)])
        string = '\n'.join([
            'Yarr, my hovercraft be full of stuff.',
            "Also, I be feelin' this pirate schtick be a mite overdone, " + \
                "me hearties.",
            '    Also: rum.'
        ])
        self.compare_steps(feature.scenarios[0].steps, [
            ('given', 'Given', 'we are testing', None, None),
            ('given', 'And', 'this is only a test', None, None),
            ('given', 'But', 'this is an important test', None, None),
            ('when', 'When', 'we test with a multiline string', string, None),
            ('then', 'Then', 'we want it to work', None, None),
        ])

        eq_(feature.scenarios[1].name, 'Gosh this is long')
        eq_(feature.scenarios[1].tags, [])
        table = model.Table(
            ['length', 'width', 'height'],
            [
                ['1', '2', '3'],
                ['4', '5', '6'],
            ]
        )
        eq_(feature.scenarios[1].examples[0].name, 'Initial')
        eq_(feature.scenarios[1].examples[0].table, table)
        table = model.Table(
            ['length', 'width', 'height'],
            [
                ['7', '8', '9'],
            ]
        )
        eq_(feature.scenarios[1].examples[1].name, 'Subsequent')
        eq_(feature.scenarios[1].examples[1].table, table)
        self.compare_steps(feature.scenarios[1].steps, [
            ('given', 'Given', 'this is <length>', None, None),
            ('then', 'Then', 'we want it to be <width>', None, None),
            ('then', 'But', 'not <height>', None, None),
        ])

        eq_(feature.scenarios[2].name, "This one doesn't have a tag")
        eq_(feature.scenarios[2].tags, [])
        self.compare_steps(feature.scenarios[2].steps, [
            ('given', 'Given', "we don't have a tag", None, None),
            ('then', 'Then', "we don't really mind", None, None),
        ])

        table = model.Table(
            ['Stuff', 'Things'],
            [
                ['wool', 'felt'],
                ['cotton', 'thread'],
                ['wood', 'paper'],
                ['explosives', 'hilarity'],
            ]
        )
        eq_(feature.scenarios[3].name, 'Doing all sorts of stuff')
        eq_(feature.scenarios[3].tags, [model.Tag(u'stuff', 1), model.Tag(u'derp', 1)])
        eq_(feature.scenarios[3].examples[0].name, 'Some stuff')
        eq_(feature.scenarios[3].examples[0].table, table)
        table = model.Table(
            ['a', 'b', 'c', 'd', 'e'],
            [
                ['1', '2', '3', '4', '5'],
                ['6', '7', '8', '9', '10'],
            ]
        )
        self.compare_steps(feature.scenarios[3].steps, [
            ('given', 'Given', 'we have <Stuff>', None, None),
            ('when', 'When', 'we do stuff with a table', None, table),
            ('then', 'Then', 'we have <Things>', None, None),
        ])


    def test_fails_to_parse_when_and_is_out_of_order(self):
        doc = u"""
Feature: Stuff

  Scenario: Failing at stuff
    And we should fail
""".lstrip()
        assert_raises(parser.ParserError, parser.parse_feature, doc)

    def test_fails_to_parse_when_but_is_out_of_order(self):
        doc = u"""
Feature: Stuff

  Scenario: Failing at stuff
    But we shall fail
""".lstrip()
        assert_raises(parser.ParserError, parser.parse_feature, doc)

    def test_fails_to_parse_when_examples_is_in_the_wrong_place(self):
        doc = u"""
Feature: Stuff

  Scenario: Failing at stuff
    But we shall fail

    Examples: Failure
      | Fail | Wheel|
""".lstrip()
        assert_raises(parser.ParserError, parser.parse_feature, doc)

class TestForeign(Common):
    def test_parses_french(self):
        doc = u"""
Fonctionnalit\xe9: testing stuff
  Oh my god, it's full of stuff...

  Contexte:
    Soit I found some stuff

  Sc\xe9nario: test stuff
    Soit I am testing stuff
    Alors it should work

  Sc\xe9nario: test more stuff
    Soit I am testing stuff
    Alors it will work
""".lstrip()
        feature = parser.parse_feature(doc, 'fr')
        eq_(feature.name, "testing stuff")
        eq_(feature.description, ["Oh my god, it's full of stuff..."])
        assert(feature.background)
        self.compare_steps(feature.background.steps, [
            ('given', 'Soit', 'I found some stuff', None, None),
        ])

        assert(len(feature.scenarios) == 2)
        eq_(feature.scenarios[0].name, 'test stuff')
        self.compare_steps(feature.scenarios[0].steps, [
            ('given', 'Soit', 'I am testing stuff', None, None),
            ('then', 'Alors', 'it should work', None, None),
        ])

    def test_parses_french_multi_word(self):
        doc = u"""
Fonctionnalit\xe9: testing stuff
  Oh my god, it's full of stuff...

  Sc\xe9nario: test stuff
    Etant donn\xe9 I am testing stuff
    Alors it should work
""".lstrip()
        feature = parser.parse_feature(doc, 'fr')
        eq_(feature.name, "testing stuff")
        eq_(feature.description, ["Oh my god, it's full of stuff..."])

        assert(len(feature.scenarios) == 1)
        eq_(feature.scenarios[0].name, 'test stuff')
        self.compare_steps(feature.scenarios[0].steps, [
            ('given', u'Etant donn\xe9', 'I am testing stuff', None, None),
            ('then', 'Alors', 'it should work', None, None),
        ])
    test_parses_french_multi_word.go=1

