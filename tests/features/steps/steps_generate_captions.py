"""BDD steps for generating captions for images."""

from behave import given, then, when


@given("a set of images to generate captions for")
def step_given_images(context):
    pass


@when("I run the caption generation process")
def step_when_generate_captions(context):
    pass


@then("captions should be generated for each image")
def step_then_captions_generated(context):
    pass
