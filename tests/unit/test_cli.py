from typer.testing import CliRunner

from gen_captions.cli import app

runner = CliRunner()


def test_cli_no_args():
    """Ensure the CLI shows help when no args."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Usage" in result.output


def test_cli_gen_env(tmp_path, monkeypatch):
    """Test 'gen_captions gen-env' command."""
    # Simulate an existing .env in the current dir
    (tmp_path / ".env").write_text("OPENAI_API_KEY=abc123\n")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["gen-env"])
    assert result.exit_code == 0
    # Should create .env1 or similar
    assert (
        "Created .env1" in result.output
        or "Created .env" in result.output
    )
