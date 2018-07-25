from behave import step, use_step_matcher

use_step_matcher("re")

@step("I print the tags")
def print_tags(context):
    print(context.detected_tags)


@step("I see the tag (.*)")
def check_tag(context, tag):
    assert tag in context.detected_tags, "Tag {} is not detected".format(tag)
