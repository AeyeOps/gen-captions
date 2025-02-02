import os
import tempfile
from unittest.mock import MagicMock

from rich.console import Console

from gen_captions.encoding_fixer import fix_encoding_issues


def test_fix_encoding_issues():
    logger = MagicMock()
    console = Console(record=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        # Make a text file with cp1252-encoded data
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "wb") as f:
            f.write(b"Hello \x96 world")  # 0x96 is a typical cp1252 dash

        # Run the encoding fixer on the directory
        fix_encoding_issues(
            caption_dir=tmpdir,
            config_dir=tmpdir,
            logger=logger,
            console=console,
        )

        # The file should now be valid UTF-8
        with open(test_file, "rb") as f:
            data = f.read()
            # Should not contain raw \x96
            assert b"\x96" not in data
