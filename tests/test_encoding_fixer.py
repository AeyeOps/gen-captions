# tests/test_encoding_fixer.py

import os
import tempfile

from gen_captions.encoding_fixer import fix_encoding_issues


def test_fix_encoding_issues():
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, "test.txt")
        # Write text with specific encoding
        with open(file_path, "w", encoding="latin1") as wf:
            wf.write("Café")
        fix_encoding_issues(tmp_dir, tmp_dir)
        # Read back and check encoding
        with open(file_path, encoding="utf-8") as rf:
            content = rf.read()
            assert content == "Café"
