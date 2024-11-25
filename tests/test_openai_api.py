# tests/test_openai_api.py

from unittest.mock import patch, mock_open
from gen_captions.openai_api import generate_description

@patch('gen_captions.openai_api.client.chat.completions.create')
@patch('builtins.open', new_callable=mock_open, read_data=b"image data")
def test_generate_description_success(mock_open, mock_create):
    mock_create.return_value = {
        'choices': [
            {
                'message': {
                    'content': 'This is a test description.'
                }
            }
        ]
    }
    description = generate_description("test_image.jpg")
    assert description == 'This is a test description.'

@patch('gen_captions.openai_api.client.chat.completions.create')
@patch('builtins.open', new_callable=mock_open, read_data=b"image data")
def test_generate_description_failure(mock_open, mock_create):
    mock_create.side_effect = Exception("Test exception")
    description = generate_description("test_image.jpg")
    assert description is None
