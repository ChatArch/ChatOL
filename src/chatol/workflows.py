"""Callable workflow functions backing the ChatOL CLI."""

from __future__ import annotations

import os
import time
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Callable, Iterable

from chatenv import EnvStore, get_paths

from chatol.client import DEFAULT_COOKIE_NAME, OverleafClient
from chatol.config import OverleafConfig
from chatol.errors import CompileError
from chatol.models import CompileResult, Project, ProjectFile, UploadResult

SleepFn = Callable[[float], None]


def client_from_env(
    *,
    base_url: str | None = None,
    email: str | None = None,
    password: str | None = None,
    session: str | None = None,
    cookie_name: str | None = None,
    timeout: float | None = None,
    chatarch_home: str | Path | None = None,
) -> OverleafClient:
    """Build an OverleafClient from explicit args, env vars, or ChatEnv.

    Explicit arguments win, then process environment variables, then the active
    ChatEnv `overleaf` profile. Configuration keys use the Overleaf namespace;
    ChatOL-specific extras should also be named with an `OVERLEAF_*` prefix.
    """

    chatenv_values = _load_active_chatenv(chatarch_home)
    resolved_base_url = base_url or _first_value(chatenv_values, "OVERLEAF_SITE_URL")
    if not resolved_base_url:
        raise ValueError("Missing base URL. Set OVERLEAF_SITE_URL or pass --base-url.")
    timeout_value = timeout if timeout is not None else _first_value(chatenv_values, "OVERLEAF_HTTP_TIMEOUT")
    resolved_timeout = float(timeout_value) if timeout_value is not None else 30.0
    resolved_cookie_name = cookie_name or _first_value(chatenv_values, "OVERLEAF_SESSION_COOKIE_NAME") or DEFAULT_COOKIE_NAME
    resolved_session = session or _first_value(chatenv_values, "OVERLEAF_SESSION_COOKIE")
    if resolved_session:
        return OverleafClient.from_session_cookie(
            resolved_base_url,
            resolved_session,
            cookie_name=resolved_cookie_name,
            timeout=resolved_timeout,
        )

    resolved_email = email or _first_value(chatenv_values, "OVERLEAF_ADMIN_EMAIL")
    resolved_password = password or _first_value(chatenv_values, "OVERLEAF_ADMIN_PASSWORD")
    if not resolved_email or not resolved_password:
        raise ValueError("Missing credentials. Set OVERLEAF_SESSION_COOKIE or OVERLEAF_ADMIN_EMAIL/OVERLEAF_ADMIN_PASSWORD.")
    return OverleafClient.from_password(resolved_base_url, resolved_email, resolved_password, timeout=resolved_timeout)


def list_projects(client: OverleafClient | None = None, **client_kwargs: object) -> list[Project]:
    """List projects through a directly callable workflow function."""

    active_client = client or client_from_env(**client_kwargs)  # type: ignore[arg-type]
    return active_client.list_projects()


def get_project(project: str, client: OverleafClient | None = None, **client_kwargs: object) -> Project:
    """Resolve a project by name or id."""

    active_client = client or client_from_env(**client_kwargs)  # type: ignore[arg-type]
    return active_client.get_project(project)


def list_files(project: str, client: OverleafClient | None = None, **client_kwargs: object) -> list[ProjectFile]:
    """List files for a project."""

    active_client = client or client_from_env(**client_kwargs)  # type: ignore[arg-type]
    resolved = active_client.get_project(project)
    return active_client.list_files(resolved.id)


def download_project_zip(
    project: str,
    output_path: str | Path,
    *,
    client: OverleafClient | None = None,
    **client_kwargs: object,
) -> Path:
    """Download the full Overleaf project archive to a zip file."""

    active_client = client or client_from_env(**client_kwargs)  # type: ignore[arg-type]
    resolved = active_client.get_project(project)
    data = active_client.download_project_zip(resolved.id)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def pull_project(
    project: str,
    output_dir: str | Path,
    *,
    force: bool = False,
    client: OverleafClient | None = None,
    **client_kwargs: object,
) -> list[Path]:
    """Download and safely extract an Overleaf project archive."""

    active_client = client or client_from_env(**client_kwargs)  # type: ignore[arg-type]
    resolved = active_client.get_project(project)
    data = active_client.download_project_zip(resolved.id)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    return _extract_zip(data, target, force=force)


def upload_file(
    project: str,
    local_path: str | Path,
    *,
    remote_path: str | None = None,
    client: OverleafClient | None = None,
    **client_kwargs: object,
) -> UploadResult:
    """Upload one local file to the Overleaf project root."""

    active_client = client or client_from_env(**client_kwargs)  # type: ignore[arg-type]
    resolved = active_client.get_project(project)
    path = Path(local_path)
    return active_client.upload_file(resolved.id, path.read_bytes(), remote_path or path.name)


def delete_file(
    project: str,
    remote_path: str,
    *,
    client: OverleafClient | None = None,
    **client_kwargs: object,
) -> ProjectFile:
    """Delete one remote project file by path."""

    active_client = client or client_from_env(**client_kwargs)  # type: ignore[arg-type]
    resolved = active_client.get_project(project)
    return active_client.delete_file(resolved.id, remote_path)


def compile_project(
    project: str,
    *,
    client: OverleafClient | None = None,
    retry_delays: Iterable[float] = (0, 20, 45),
    sleep: SleepFn = time.sleep,
    **client_kwargs: object,
) -> tuple[Project, CompileResult]:
    """Compile a project with retry handling for Overleaf cooldowns."""

    active_client = client or client_from_env(**client_kwargs)  # type: ignore[arg-type]
    resolved = active_client.get_project(project)
    last_error: CompileError | None = None
    for delay in retry_delays:
        if delay:
            sleep(delay)
        try:
            return resolved, active_client.compile_project(resolved.id)
        except CompileError as exc:
            last_error = exc
            if not exc.retryable:
                raise
    assert last_error is not None
    raise last_error


def download_pdf(
    project: str,
    output_path: str | Path,
    *,
    client: OverleafClient | None = None,
    retry_delays: Iterable[float] = (0, 20, 45),
    sleep: SleepFn = time.sleep,
    **client_kwargs: object,
) -> Path:
    """Compile a project and write the PDF to disk."""

    active_client = client or client_from_env(**client_kwargs)  # type: ignore[arg-type]
    resolved = active_client.get_project(project)
    data = _retry_bytes(
        lambda: active_client.download_pdf(resolved.id),
        retry_delays=retry_delays,
        sleep=sleep,
    )
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def download_output(
    project: str,
    output_type: str,
    output_path: str | Path,
    *,
    client: OverleafClient | None = None,
    retry_delays: Iterable[float] = (0, 20, 45),
    sleep: SleepFn = time.sleep,
    **client_kwargs: object,
) -> Path:
    """Compile a project and write one output artifact to disk."""

    active_client = client or client_from_env(**client_kwargs)  # type: ignore[arg-type]
    resolved = active_client.get_project(project)
    data = _retry_bytes(
        lambda: active_client.download_output(resolved.id, output_type),
        retry_delays=retry_delays,
        sleep=sleep,
    )
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _retry_bytes(
    operation: Callable[[], bytes],
    *,
    retry_delays: Iterable[float],
    sleep: SleepFn,
) -> bytes:
    last_error: CompileError | None = None
    for delay in retry_delays:
        if delay:
            sleep(delay)
        try:
            return operation()
        except CompileError as exc:
            last_error = exc
            if not exc.retryable:
                raise
    assert last_error is not None
    raise last_error


def _extract_zip(data: bytes, output_dir: Path, *, force: bool) -> list[Path]:
    extracted: list[Path] = []
    output_root = output_dir.resolve()
    with zipfile.ZipFile(BytesIO(data)) as archive:
        for member in archive.infolist():
            name = member.filename
            if not name or name.endswith("/"):
                continue
            target = (output_root / name).resolve()
            if output_root not in target.parents and target != output_root:
                raise ValueError(f"Refusing unsafe zip path: {name}")
            if target.exists() and not force:
                raise FileExistsError(f"Refusing to overwrite existing file without force: {target}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))
            extracted.append(target)
    return extracted


def _load_active_chatenv(chatarch_home: str | Path | None) -> dict[str, str]:
    """Load active ChatEnv values without mutating process environment."""

    store = EnvStore(get_paths(chatarch_home).envs_dir)
    return store.load_active(OverleafConfig)


def _first_value(chatenv_values: dict[str, str], *names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    for name in names:
        value = chatenv_values.get(name)
        if value:
            return value
    return None
