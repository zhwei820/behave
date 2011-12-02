import logging
from behave import *

spam_log = logging.getLogger('spam')
ham_log = logging.getLogger('ham')

@given("I am testing stuff")
def step(context):
    context.testing_stuff = True

@given("some stuff is set up")
def step(context):
    context.stuff_set_up = True

@given("stuff has been set up")
def step(context):
    assert context.testing_stuff is True
    assert context.stuff_set_up is True

@when("I exercise it work")
def step(context):
    spam_log.error('logging!')
    ham_log.error('logging!')

@then("it will work")
def step(context):
    pass

