from click.testing import CliRunner

from chatol import __version__
from chatol.cli import main


def test_version_option_reports_package_version():
    assert main.name == "oleaf"

    result = CliRunner().invoke(main, ["--version"])

    assert result.exit_code == 0
    assert f"oleaf, version {__version__}" in result.output


def test_help_lists_primary_command_groups():
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "projects" in result.output
    assert "files" in result.output
    assert "templates" in result.output
    assert "compile" in result.output
    assert "admin" in result.output
    assert "doctor" in result.output


def test_files_help_lists_agent_flow_commands():
    result = CliRunner().invoke(main, ["files", "--help"])

    assert result.exit_code == 0
    assert "list" in result.output
    assert "zip" in result.output
    assert "pull" in result.output
    assert "upload" in result.output
    assert "delete" in result.output


def test_json_alias_is_available_on_doctor():
    result = CliRunner().invoke(main, ["doctor", "--help"])

    assert result.exit_code == 0
    assert "--json" in result.output
    assert "--json-output" in result.output


def test_templates_help_lists_template_commands():
    result = CliRunner().invoke(main, ["templates", "--help"])

    assert result.exit_code == 0
    assert "list" in result.output
    assert "init" in result.output
    assert "upload" in result.output


def test_compile_help_lists_bundle_command():
    result = CliRunner().invoke(main, ["compile", "--help"])

    assert result.exit_code == 0
    assert "bundle" in result.output


def test_admin_help_lists_doctor_command():
    result = CliRunner().invoke(main, ["admin", "--help"])

    assert result.exit_code == 0
    assert "doctor" in result.output
