from click.testing import CliRunner

from chatol import __version__
from chatol.cli import main


def test_version_option_reports_package_version():
    result = CliRunner().invoke(main, ["--version"])

    assert result.exit_code == 0
    assert f"oleaf, version {__version__}" in result.output


def test_help_lists_primary_command_groups():
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "projects" in result.output
    assert "compile" in result.output
    assert "doctor" in result.output


def test_json_alias_is_available_on_doctor():
    result = CliRunner().invoke(main, ["doctor", "--help"])

    assert result.exit_code == 0
    assert "--json" in result.output
    assert "--json-output" in result.output
