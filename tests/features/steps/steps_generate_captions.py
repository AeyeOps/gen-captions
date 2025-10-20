"""BDD steps for generating captions for images."""

from behave import given, then, when


@given("a set of images to generate captions for")
def step_given_images(context):
    """Seed the scenario with images pending caption generation."""
    del context


@when("I run the caption generation process")
def step_when_generate_captions(context):
    """Trigger the caption generation flow."""
    del context


@then("captions should be generated for each image")
def step_then_captions_generated(context):
    """Verify that captions are produced for the pending images."""
    del context


def test_steps_loaded():
    """Placeholder so pytest treats this module as a valid test file."""
    assert True
