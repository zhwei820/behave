import os.path

import yaml

from behave import model

I18N_FILE = os.path.join(os.path.dirname(__file__), 'i18n.yml')
parsers = {}


def parse_file(filename, language=None):
    with open(filename) as f:
        # file encoding is assumed to be utf8. Oh, yes.
        data = f.read().decode('utf8')
    return parse_feature(data, language, filename)


def parse_feature(data, language=None, filename=None):
    global parsers

    if not language:
        language = 'en'

    parser = parsers.get(language, None)
    if parser is None:
        parser = Parser(language)
        parsers[language] = parser

    try:
        result = parser.parse(data, filename)
    except ParserError, e:
        e.filename = filename
        raise

    return result


class ParserError(Exception):
    def __init__(self, message, line, filename=None):
        if line:
            message += ' at line {0:d}'.format(line)
        super(ParserError, self).__init__(message)
        self.line = line
        self.filename = filename

    def __str__(self):
        if self.filename:
            return 'Failed to parse "%s": %s' % (self.filename, self.message)
        return 'Failed to parse <string>: %s' % self.message


class Parser(object):
    languages = None

    def __init__(self, language):
        if Parser.languages is None:
            Parser.languages = yaml.load(open(I18N_FILE))
        if language not in Parser.languages:
            raise ParserError("Unknown language: " + repr(language), None)
        self.keywords = Parser.languages[language]
        for k, v in self.keywords.items():
            self.keywords[k] = v.split('|')
        self.step_keywords = {}
        for k in ('given', 'when', 'then', 'and', 'but'):
            for kw in self.keywords[k]:
                if kw in self.step_keywords:
                    self.step_keywords[kw] = 'step'
                else:
                    self.step_keywords[kw] = k

        self.reset()

    def reset(self):
        self.state = 'init'
        self.line = 0
        self.last_step = None
        self.multiline_leading = None
        self.multiline_terminator = None

        self.filename = None
        self.feature = None
        self.statement = None
        self.tags = []
        self.lines = []
        self.table = None
        self.examples = None

    def parse(self, data, filename=None):
        self.reset()

        self.filename = filename

        for line in data.split('\n'):
            self.line += 1
            if not line.strip():
                continue
            self.action(line)

        if self.table:
            self.action_table('')

        feature = self.feature
        feature.parser = self
        self.reset()
        return feature

    def action(self, line):
        func = getattr(self, 'action_' + self.state, None)
        if func is None:
            raise ParserError('Parser in unknown state ' + self.state,
                              self.line)
        if not func(line):
            raise ParserError("Parser failure in state " + self.state,
                              self.line)

    def action_init(self, line):
        line = line.strip()

        if line.startswith('@'):
            self.tags.extend([tag.strip() for tag in line[1:].split('@')])
            return True
        feature_kwd = self.match_keyword('feature', line)
        if feature_kwd:
            name = line[len(feature_kwd) + 1:].strip()
            self.feature = model.Feature(self.filename, self.line, feature_kwd,
                                         name, tags=self.tags)
            self.tags = []
            self.state = 'feature'
            return True
        return False

    def action_feature(self, line):
        line = line.strip()

        if line.startswith('@'):
            self.tags.extend([tag.strip() for tag in line[1:].split('@')])
            return True

        background_kwd = self.match_keyword('background', line)
        if background_kwd:
            name = line[len(background_kwd) + 1:].strip()
            self.statement = model.Background(self.filename, self.line,
                                              background_kwd, name)
            self.feature.background = self.statement
            self.state = 'steps'
            return True

        scenario_kwd = self.match_keyword('scenario', line)
        if scenario_kwd:
            name = line[len(scenario_kwd) + 1:].strip()
            self.statement = model.Scenario(self.filename, self.line,
                                            scenario_kwd, name, tags=self.tags)
            self.tags = []
            self.feature.add_scenario(self.statement)
            self.state = 'steps'
            return True

        scenario_outline_kwd = self.match_keyword('scenario_outline', line)
        if scenario_outline_kwd:
            name = line[len(scenario_outline_kwd) + 1:].strip()
            self.statement = model.ScenarioOutline(self.filename, self.line,
                                                   scenario_outline_kwd, name,
                                                   tags=self.tags)
            self.tags = []
            self.feature.add_scenario(self.statement)
            self.state = 'steps'
            return True

        self.feature.description.append(line)
        return True

    def action_steps(self, line):
        stripped = line.lstrip()
        if stripped.startswith('"""') or stripped.startswith("'''"):
            self.state = 'multiline'
            self.multiline_terminator = stripped[:3]
            self.multiline_leading = line.index(stripped[0])
            return True

        line = line.strip()

        step = self.parse_step(line)
        if step:
            self.statement.steps.append(step)
            return True

        if line.startswith('@'):
            self.tags.extend([tag.strip() for tag in line[1:].split('@')])
            return True

        scenario_kwd = self.match_keyword('scenario', line)
        if scenario_kwd:
            name = line[len(scenario_kwd) + 1:].strip()
            self.statement = model.Scenario(self.filename, self.line,
                                            scenario_kwd, name, tags=self.tags)
            self.tags = []
            self.feature.add_scenario(self.statement)
            return True

        scenario_outline_kwd = self.match_keyword('scenario_outline', line)
        if scenario_outline_kwd:
            name = line[len(scenario_outline_kwd) + 1:].strip()
            self.statement = model.ScenarioOutline(self.filename, self.line,
                                                   scenario_outline_kwd, name,
                                                   tags=self.tags)
            self.tags = []
            self.feature.add_scenario(self.statement)
            self.state = 'steps'
            return True

        examples_kwd = self.match_keyword('examples', line)
        if examples_kwd:
            if not isinstance(self.statement, model.ScenarioOutline):
                message = 'Examples must only appear inside scenario outline'
                raise ParserError(message, self.line)
            name = line[len(examples_kwd) + 1:].strip()
            self.examples = model.Examples(self.filename, self.line,
                                           examples_kwd, name)
            self.statement.examples.append(self.examples)
            self.state = 'table'
            return True

        if line.startswith('|'):
            self.state = 'table'
            return self.action_table(line)

        return False

    def action_multiline(self, line):
        if line.strip().startswith(self.multiline_terminator):
            step = self.statement.steps[-1]
            step.string = '\n'.join(self.lines)
            if step.name.endswith(':'):
                step.name = step.name[:-1]
            self.lines = []
            self.multiline_terminator = None
            self.state = 'steps'
            return True

        self.lines.append(line[self.multiline_leading:])
        return True

    def action_table(self, line):
        line = line.strip()

        if not line.startswith('|'):
            if self.examples:
                self.examples.table = self.table
                self.examples = None
            else:
                step = self.statement.steps[-1]
                step.table = self.table
                if step.name.endswith(':'):
                    step.name = step.name[:-1]
            self.table = None
            self.state = 'steps'
            return self.action_steps(line)

        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        if self.table is None:
            self.table = model.Table(cells)
        else:
            if len(cells) != len(self.table.headings):
                raise ParserError("Malformed table", self.line)
            self.table.rows.append(cells)
        return True

    def match_keyword(self, keyword, line):
        for alias in self.keywords[keyword]:
            if line.startswith(alias + ':'):
                return alias
        return False

    def parse_step(self, line):
        for kw in self.step_keywords:
            if line.startswith(kw):
                name = line[len(kw):].strip()
                step_type = self.step_keywords[kw]
                if step_type in ('and', 'but'):
                    if not self.last_step:
                        raise ParserError("No previous step", self.line)
                    step_type = self.last_step
                else:
                    self.last_step = step_type
                step = model.Step(self.filename, self.line, kw, step_type,
                                  name)
                return step
        return None
