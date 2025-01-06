# tests/test_cli.py

import sys
from unittest.mock import patch

from gen_captions.cli import config_arg_parser


def test_config_arg_parser():
    test_args = [
        "program",
        "--image-dir",
        "/path/to/images",
        "--caption-dir",
        "/path/to/captions",
        "--config-dir",
        "/path/to/config",
    ]
    with patch.object(sys, "argv", test_args):
        parser = config_arg_parser()
        args = parser.parse_args()
        assert args.image_dir == "/path/to/images"
        assert args.caption_dir == "/path/to/captions"
        assert args.config_dir == "/path/to/config"
