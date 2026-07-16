"""CLI entrypoint for chatol."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

from chatol import __version__
from chatol.errors import ChatOLError
from chatol.workflows import client_from_env, compile_project, download_output, download_pdf, get_project, list_projects


@click.group()
@click.version_option(__version__, prog_name="chatol")
@click.option("--base-url", help="Overleaf instance base URL. Defaults to CHATOL_BASE_URL/OVERLEAF_BASE_URL.")
@click.option("--email", help="Account email. Defaults to CHATOL_EMAIL/OVERLEAF_EMAIL.")
@click.option("--password-stdin", is_flag=True, help="Read the account password from stdin.")
@click.option("--session-stdin", is_flag=True, help="Read an Overleaf session cookie from stdin.")
@click.option("--cookie-name", help="Session cookie name. Defaults to overleaf_session2.")
@click.option("--timeout", type=float, help="HTTP timeout in seconds.")
@click.pass_context
def main(ctx: click.Context, **options: Any) -> None:
    """ChatOL command line interface.

    Every CLI command is a thin wrapper over importable functions in
    `chatol.workflows` or methods on `chatol.client.OverleafClient`.
    """

    password = sys.stdin.readline().rstrip("\n") if options.pop("password_stdin") else None
    session = sys.stdin.readline().strip() if options.pop("session_stdin") else None
    ctx.obj = {
        "base_url": options.get("base_url"),
        "email": options.get("email"),
        "password": password,
        "session": session,
        "cookie_name": options.get("cookie_name"),
        "timeout": options.get("timeout"),
    }


@main.command()
@click.option("--json", "--json-output", "as_json", is_flag=True, help="Output machine-readable JSON.")
@click.pass_context
def doctor(ctx: click.Context, as_json: bool) -> None:
    """Validate login and project-list access."""

    try:
        client = client_from_env(**_client_kwargs(ctx))
        projects = client.list_projects()
        result = {"ok": True, "project_count": len(projects)}
        _emit(result, as_json=as_json)
    except Exception as exc:  # noqa: BLE001 - CLI boundary converts to stable error output.
        _handle_error(exc, as_json=as_json)


@main.group()
def projects() -> None:
    """Project discovery commands."""


@projects.command("list")
@click.option("--json", "--json-output", "as_json", is_flag=True, help="Output machine-readable JSON.")
@click.pass_context
def projects_list(ctx: click.Context, as_json: bool) -> None:
    """List projects visible to the current session."""

    try:
        items = list_projects(**_client_kwargs(ctx))
        payload = [project.to_dict() for project in items]
        _emit(payload, as_json=as_json)
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, as_json=as_json)


@projects.command("info")
@click.argument("project")
@click.option("--json", "--json-output", "as_json", is_flag=True, help="Output machine-readable JSON.")
@click.pass_context
def projects_info(ctx: click.Context, project: str, as_json: bool) -> None:
    """Resolve a project by name or id."""

    try:
        resolved = get_project(project, **_client_kwargs(ctx))
        _emit(resolved.to_dict(), as_json=as_json)
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, as_json=as_json)


@main.group(name="compile")
def compile_group() -> None:
    """Compile and output artifact commands."""


@compile_group.command("run")
@click.argument("project")
@click.option("--json", "--json-output", "as_json", is_flag=True, help="Output machine-readable JSON.")
@click.pass_context
def compile_run(ctx: click.Context, project: str, as_json: bool) -> None:
    """Compile a project and report output metadata."""

    try:
        resolved, result = compile_project(project, **_client_kwargs(ctx))
        payload = {"project": resolved.to_dict(), "compile": result.to_dict()}
        _emit(payload, as_json=as_json)
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, as_json=as_json)


@compile_group.command("pdf")
@click.argument("project")
@click.option("-o", "--output", required=True, type=click.Path(path_type=Path), help="PDF output path.")
@click.option("--json", "--json-output", "as_json", is_flag=True, help="Output machine-readable JSON.")
@click.pass_context
def compile_pdf(ctx: click.Context, project: str, output: Path, as_json: bool) -> None:
    """Compile a project and download its PDF."""

    try:
        path = download_pdf(project, output, **_client_kwargs(ctx))
        _emit({"ok": True, "output": str(path), "bytes": path.stat().st_size}, as_json=as_json)
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, as_json=as_json)


@compile_group.command("output")
@click.argument("project")
@click.argument("output_type")
@click.option("-o", "--output", required=True, type=click.Path(path_type=Path), help="Artifact output path.")
@click.option("--json", "--json-output", "as_json", is_flag=True, help="Output machine-readable JSON.")
@click.pass_context
def compile_output(ctx: click.Context, project: str, output_type: str, output: Path, as_json: bool) -> None:
    """Compile a project and download one output artifact."""

    try:
        path = download_output(project, output_type, output, **_client_kwargs(ctx))
        _emit(
            {"ok": True, "output_type": output_type, "output": str(path), "bytes": path.stat().st_size},
            as_json=as_json,
        )
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, as_json=as_json)


def _client_kwargs(ctx: click.Context) -> dict[str, Any]:
    return {key: value for key, value in (ctx.obj or {}).items() if value is not None}


def _emit(data: Any, *, as_json: bool) -> None:
    if as_json:
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                click.echo(item.get("name") or json.dumps(item, ensure_ascii=False))
            else:
                click.echo(str(item))
        return
    if isinstance(data, dict):
        for key, value in data.items():
            click.echo(f"{key}: {value}")
        return
    click.echo(str(data))


def _handle_error(exc: Exception, *, as_json: bool) -> None:
    code = exc.code if isinstance(exc, ChatOLError) else exc.__class__.__name__.lower()
    payload = {"ok": False, "error": {"code": code, "message": str(exc)}}
    if as_json:
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2), err=True)
    else:
        click.echo(f"Error [{code}]: {exc}", err=True)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
