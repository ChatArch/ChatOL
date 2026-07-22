"""CLI entrypoint for the oleaf command."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

from chatol import __version__
from chatol.errors import ChatOLError
from chatol.workflows import (
    admin_status,
    client_from_env,
    compile_project,
    delete_file,
    download_compile_bundle,
    download_output,
    download_pdf,
    download_project_zip,
    get_project,
    list_files,
    list_projects,
    list_templates,
    pull_project,
    upload_template,
    upload_file,
    write_template,
)


@click.group(name="oleaf")
@click.version_option(__version__)
@click.option("--base-url", help="Overleaf instance base URL. Defaults to OVERLEAF_SITE_URL.")
@click.option("--email", help="Account email. Defaults to OVERLEAF_ADMIN_EMAIL.")
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


@main.group()
def files() -> None:
    """Project file and archive commands."""


@files.command("list")
@click.argument("project")
@click.option("--json", "--json-output", "as_json", is_flag=True, help="Output machine-readable JSON.")
@click.pass_context
def files_list(ctx: click.Context, project: str, as_json: bool) -> None:
    """List file-like project entities when supported by the instance."""

    try:
        items = list_files(project, **_client_kwargs(ctx))
        _emit([item.to_dict() for item in items], as_json=as_json)
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, as_json=as_json)


@files.command("zip")
@click.argument("project")
@click.option("-o", "--output", required=True, type=click.Path(path_type=Path), help="Zip output path.")
@click.option("--json", "--json-output", "as_json", is_flag=True, help="Output machine-readable JSON.")
@click.pass_context
def files_zip(ctx: click.Context, project: str, output: Path, as_json: bool) -> None:
    """Download the full project zip archive."""

    try:
        path = download_project_zip(project, output, **_client_kwargs(ctx))
        _emit({"ok": True, "output": str(path), "bytes": path.stat().st_size}, as_json=as_json)
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, as_json=as_json)


@files.command("pull")
@click.argument("project")
@click.argument("output_dir", type=click.Path(path_type=Path, file_okay=False))
@click.option("--force", is_flag=True, help="Overwrite existing local files.")
@click.option("--json", "--json-output", "as_json", is_flag=True, help="Output machine-readable JSON.")
@click.pass_context
def files_pull(ctx: click.Context, project: str, output_dir: Path, force: bool, as_json: bool) -> None:
    """Download and extract the full project archive."""

    try:
        paths = pull_project(project, output_dir, force=force, **_client_kwargs(ctx))
        _emit(
            {"ok": True, "output_dir": str(output_dir), "files": [str(path) for path in paths], "count": len(paths)},
            as_json=as_json,
        )
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, as_json=as_json)


@files.command("upload")
@click.argument("project")
@click.argument("local_path", type=click.Path(path_type=Path, dir_okay=False, exists=True))
@click.option("--remote-path", help="Remote filename. Nested paths are not implemented yet.")
@click.option("--json", "--json-output", "as_json", is_flag=True, help="Output machine-readable JSON.")
@click.pass_context
def files_upload(ctx: click.Context, project: str, local_path: Path, remote_path: str | None, as_json: bool) -> None:
    """Upload one local file to the project root."""

    try:
        result = upload_file(project, local_path, remote_path=remote_path, **_client_kwargs(ctx))
        payload = {"ok": True, **result.to_dict()}
        _emit(payload, as_json=as_json)
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, as_json=as_json)


@files.command("delete")
@click.argument("project")
@click.argument("remote_path")
@click.option("--apply", is_flag=True, help="Actually delete the remote file. Required.")
@click.option("--json", "--json-output", "as_json", is_flag=True, help="Output machine-readable JSON.")
@click.pass_context
def files_delete(ctx: click.Context, project: str, remote_path: str, apply: bool, as_json: bool) -> None:
    """Delete one remote file by path; requires --apply."""

    try:
        if not apply:
            raise click.ClickException("Refusing to delete without --apply.")
        deleted = delete_file(project, remote_path, **_client_kwargs(ctx))
        _emit({"ok": True, "deleted": deleted.to_dict()}, as_json=as_json)
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, as_json=as_json)


@main.group()
def templates() -> None:
    """Local template commands."""


@templates.command("list")
@click.option("--json", "--json-output", "as_json", is_flag=True, help="Output machine-readable JSON.")
def templates_list(as_json: bool) -> None:
    """List built-in templates."""

    try:
        items = list_templates()
        _emit([item.to_dict() for item in items], as_json=as_json)
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, as_json=as_json)


@templates.command("init")
@click.argument("template")
@click.argument("output_dir", type=click.Path(path_type=Path, file_okay=False))
@click.option("--force", is_flag=True, help="Overwrite existing local template files.")
@click.option("--json", "--json-output", "as_json", is_flag=True, help="Output machine-readable JSON.")
def templates_init(template: str, output_dir: Path, force: bool, as_json: bool) -> None:
    """Write a built-in template to a local directory."""

    try:
        paths = write_template(template, output_dir, force=force)
        _emit({"ok": True, "template": template, "files": [str(path) for path in paths]}, as_json=as_json)
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, as_json=as_json)


@templates.command("upload")
@click.argument("project")
@click.argument("template_dir", type=click.Path(path_type=Path, file_okay=False, exists=True))
@click.option("--json", "--json-output", "as_json", is_flag=True, help="Output machine-readable JSON.")
@click.pass_context
def templates_upload(ctx: click.Context, project: str, template_dir: Path, as_json: bool) -> None:
    """Upload root-level template files to an Overleaf project."""

    try:
        results = upload_template(project, template_dir, **_client_kwargs(ctx))
        _emit({"ok": True, "uploaded": [result.to_dict() for result in results]}, as_json=as_json)
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc, as_json=as_json)


@main.group()
def admin() -> None:
    """Read-only admin and user-management probes."""


@admin.command("doctor")
@click.option("--json", "--json-output", "as_json", is_flag=True, help="Output machine-readable JSON.")
@click.pass_context
def admin_doctor(ctx: click.Context, as_json: bool) -> None:
    """Probe admin availability without changing users or projects."""

    try:
        status = admin_status(**_client_kwargs(ctx))
        _emit(status.to_dict(), as_json=as_json)
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


@compile_group.command("bundle")
@click.argument("project")
@click.option("-o", "--output-dir", required=True, type=click.Path(path_type=Path, file_okay=False), help="Directory for downloaded artifacts.")
@click.option("--output-type", "output_types", multiple=True, default=("pdf", "log"), help="Compile output type to download. Can be repeated.")
@click.option("--include-source-zip", is_flag=True, help="Also download the project source zip.")
@click.option("--json", "--json-output", "as_json", is_flag=True, help="Output machine-readable JSON.")
@click.pass_context
def compile_bundle(
    ctx: click.Context,
    project: str,
    output_dir: Path,
    output_types: tuple[str, ...],
    include_source_zip: bool,
    as_json: bool,
) -> None:
    """Compile once and download several common paper artifacts."""

    try:
        result = download_compile_bundle(
            project,
            output_dir,
            output_types=output_types,
            include_project_zip=include_source_zip,
            **_client_kwargs(ctx),
        )
        payload = {"ok": True, **result.to_dict()}
        _emit(payload, as_json=as_json)
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
