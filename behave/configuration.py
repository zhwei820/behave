import argparse
import sys

from behave.tag_expression import TagExpression


class ConfigError(Exception):
    pass

usage = "%(prog)s [options] [ [FILE|DIR|URL][:LINE[:LINE]*] ]+"
parser = argparse.ArgumentParser(usage=usage)

parser.add_argument('-b', '--backtrace', action='store_true',
                    help="Show full backtraces for all errors.")
parser.add_argument('-c', '--no-color', action='store_true',
                    help="Disable the use of ANSI color escapes.")
parser.add_argument('-d', '--dry-run', action='store_true',
                    help="Invokes formatters without executing the steps.")
parser.add_argument('-e', '--exclude', metavar="PATTERN",
                    help="Don't run feature files matching PATTERN.")
parser.add_argument('-f', '--format', action='append',
                    help="""Add a formatter. By default, only a 'pretty'
                            formatter is used. Pass '--format help' to get a
                            list of available formatters.""")
parser.add_argument('-g', '--guess', action='store_true',
                    help="Guess best match for ambiguous steps.")
parser.add_argument('-i', '--no-snippets', action='store_true',
                    help="Don't print snippets for pending steps.")
parser.add_argument('-m', '--no-multiline', action='store_true',
                    help="""Don't print multiline strings and tables under
                            steps.""")
parser.add_argument('-n', '--name', action="append",
                    help="""Only execute the feature elements which match part
                            of the given name. If this option is given more
                            than once, it will match against all the given
                            names.""")
parser.add_argument('--nocapture', action='store_false', dest='stdout_capture',
                    default=True,
                    help="""Don't capture stdout (any stdout output will be
                            printed immediately.)""")
parser.add_argument('--nologcapture', action='store_false', dest='log_capture',
                    default=True,
                    help="""Don't capture logging. Logging configuration will
                            be left intact.""")
parser.add_argument('--logging-format',
                    help="""Specify custom format to print statements. Uses the
                        same format as used by standard logging handlers. The
                        default is '%%(levelname)s:%%(name)s:%%(message)s'.""")
parser.add_argument('--logging-level',
                    help="""Specify a level to capture logging at. The default
                        is NOTSET - capturing everything.""")
parser.add_argument('--logging-datefmt',
                    help="""Specify custom date/time format to print
                            statements.
                            Uses the same format as used by standard logging
                            handlers.""")
parser.add_argument('--logging-filter',
                    help="""
                        Specify which statements to filter in/out. By default,
                        everything is captured. If the output is too verbose,
                        use this option to filter out needless output.
                        Example: --logging-filter=foo will capture statements
                        issued ONLY to foo or foo.what.ever.sub but not foobar
                        or other logger. Specify multiple loggers with comma:
                        filter=foo,bar,baz. If any logger name is prefixed
                        with a minus, eg filter=-foo, it will be excluded
                        rather than included.""")
parser.add_argument('--logging-clear-handlers', action='store_true',
                        help="Clear all other logging handlers")
parser.add_argument('-o', '--outfile', metavar='FILE',
                    help="Write to specified file instead of stdout.")
parser.add_argument('-q', '--quiet', action='store_true',
                    help="Alias for --no-snippets --no-source.")
parser.add_argument('-s', '--no-source', action='store_true',
                    help="""Don't print the file and line of the step
                            definition with the steps.""")
parser.add_argument('--stop', action='store_true',
                    help='Stop running tests at the first failure.')
parser.add_argument('-S', '--strict', action='store_true',
                    help='Fail if there are any undefined or pending steps.')
parser.add_argument('-t', '--tags', action='append', metavar='TAG_EXPRESSION',
                    help="""Only execute features or scenarios with tags
                            matching TAG_EXPRESSION. Pass '--tag-help' for
                            more information.""")
parser.add_argument('-v', '--verbose', action='store_true',
                    help='Show the files and features loaded.')
parser.add_argument('-w', '--wip', action='store_true',
                    help="Fail if there are any passing scenarios.")
parser.add_argument('-x', '--expand', action='store_true',
                    help="Expand scenario outline tables in output.")
parser.add_argument('--lang', metavar='LANG',
                    help="Use keywords for a language other than English.")
parser.add_argument('--lang-list', action='store_true',
                    help="List the languages abailable for --lang")
parser.add_argument('--lang-help', metavar='LANG',
                    help="List the translations accepted for one language.")
parser.add_argument('--tags-help', action='store_true',
                    help="Show help for tag expressions.")
parser.add_argument('--version', action='store_true', help="Show version.")

parser.add_argument('paths', nargs='*')


class Configuration(object):
    def __init__(self):
        self.formatters = []

        args = parser.parse_args()
        for key, value in args.__dict__.items():
            if key.startswith('_'):
                continue
            setattr(self, key, value)

        if args.outfile and args.outfile != '-':
            self.output = open(args.outfile, 'w')
        else:
            self.output = sys.stdout

        self.tags = TagExpression(self.tags or [])
