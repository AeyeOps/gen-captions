Feature: Generate image captions
  In order to produce detailed captions for images using an LLM
  As a CLI user
  I want to run "get-captions generate" with a chosen backend

  Scenario: Captions are generated successfully
    Given I have a directory of images in "test_images/"
    And I have set the environment variable "OPENAI_API_KEY" to "fake-key"
    When I run the CLI command "get-captions generate --image-dir test_images --caption-dir output --llm-backend openai"
    Then a text file should be created in "output" for each image
    And each text file should contain "[trigger]"
