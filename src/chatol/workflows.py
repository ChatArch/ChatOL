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
from chatol.models import (
    AdminStatus,
    CompileBundleResult,
    CompileResult,
    DownloadedArtifact,
    Project,
    ProjectFile,
    TemplateSpec,
    UploadResult,
)

SleepFn = Callable[[float], None]

_TEMPLATES: dict[str, dict[str, object]] = {
    "article-basic": {
        "description": "Minimal article template with bibliography support.",
        "files": {
            "main.tex": """\\documentclass{article}
\\usepackage[utf8]{inputenc}
\\usepackage{graphicx}
\\usepackage{hyperref}

\\title{Paper Title}
\\author{Author Name}
\\date{\\today}

\\begin{document}
\\maketitle

\\begin{abstract}
Write the abstract here.
\\end{abstract}

\\section{Introduction}
This is a minimal ChatOL article template. Cite an example~\\cite{example2026}.

\\bibliographystyle{plain}
\\bibliography{references}

\\end{document}
""",
            "references.bib": """@article{example2026,
  title={Example Reference},
  author={Author, Alice},
  journal={Journal of Examples},
  year={2026}
}
""",
        },
    },
    "latex-note": {
        "description": "Small note template for quick compile checks.",
        "files": {
            "main.tex": """\\documentclass{article}
\\usepackage[utf8]{inputenc}

\\title{Quick Note}
\\author{Author Name}
\\date{\\today}

\\begin{document}
\\maketitle

\\section{Note}
Write a short note here.

\\end{document}
""",
        },
    },
}


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


def list_templates() -> list[TemplateSpec]:
    """Return built-in templates available for local initialization."""

    specs: list[TemplateSpec] = []
    for name, data in sorted(_TEMPLATES.items()):
        files = data.get("files")
        if not isinstance(files, dict):
            continue
        specs.append(
            TemplateSpec(
                name=name,
                description=str(data.get("description") or ""),
                files=tuple(sorted(str(path) for path in files)),
            )
        )
    return specs


def write_template(template: str, output_dir: str | Path, *, force: bool = False) -> list[Path]:
    """Write a built-in template to a local directory."""

    files = _template_files(template)
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for relative_path, content in files.items():
        if "/" in relative_path or "\\" in relative_path or relative_path.startswith("."):
            raise ValueError(f"Refusing unsafe template path: {relative_path}")
        target = target_dir / relative_path
        if target.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite existing file without force: {target}")
        target.write_text(content, encoding="utf-8")
        written.append(target)
    return written


def upload_template(
    project: str,
    template_dir: str | Path,
    *,
    client: OverleafClient | None = None,
    **client_kwargs: object,
) -> list[UploadResult]:
    """Upload root-level template files from a local directory."""

    root = Path(template_dir)
    if not root.is_dir():
        raise NotADirectoryError(f"Template directory not found: {root}")
    active_client = client or client_from_env(**client_kwargs)  # type: ignore[arg-type]
    resolved = active_client.get_project(project)
    results: list[UploadResult] = []
    for path in sorted(item for item in root.iterdir() if item.is_file() and not item.name.startswith(".")):
        results.append(active_client.upload_file(resolved.id, path.read_bytes(), path.name))
    if not results:
        raise FileNotFoundError(f"No root-level template files found in: {root}")
    return results


def admin_status(client: OverleafClient | None = None, **client_kwargs: object) -> AdminStatus:
    """Probe admin/user-management availability without mutating state."""

    active_client = client or client_from_env(**client_kwargs)  # type: ignore[arg-type]
    return active_client.admin_status()


def download_compile_bundle(
    project: str,
    output_dir: str | Path,
    *,
    output_types: Iterable[str] = ("pdf", "log"),
    include_project_zip: bool = False,
    client: OverleafClient | None = None,
    retry_delays: Iterable[float] = (0, 20, 45),
    sleep: SleepFn = time.sleep,
    **client_kwargs: object,
) -> CompileBundleResult:
    """Compile once and download several common paper artifacts."""

    active_client = client or client_from_env(**client_kwargs)  # type: ignore[arg-type]
    resolved = active_client.get_project(project)
    _, result = compile_project(resolved.id, client=active_client, retry_delays=retry_delays, sleep=sleep)
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    artifacts: list[DownloadedArtifact] = []

    for output_type in output_types:
        requested = output_type.strip().lstrip(".").lower()
        if not requested:
            continue
        output = result.pdf_output() if requested == "pdf" else result.find_output(requested)
        if not output:
            raise CompileError("output_not_found", f"No output found for {output_type}")
        filename = _safe_output_name(output.path or f"output.{requested}", default=f"output.{requested}")
        path = target_dir / filename
        data = active_client.download_compile_output(output, result)
        path.write_bytes(data)
        artifacts.append(DownloadedArtifact(requested, str(path), len(data)))

    if include_project_zip:
        data = active_client.download_project_zip(resolved.id)
        path = target_dir / "project.zip"
        path.write_bytes(data)
        artifacts.append(DownloadedArtifact("project_zip", str(path), len(data)))

    return CompileBundleResult(project=resolved, compile=result, artifacts=artifacts)


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


def _template_files(template: str) -> dict[str, str]:
    data = _TEMPLATES.get(template)
    if not data:
        available = ", ".join(sorted(_TEMPLATES))
        raise ValueError(f"Unknown template: {template}. Available templates: {available}")
    files = data.get("files")
    if not isinstance(files, dict):
        raise ValueError(f"Template has no files: {template}")
    return {str(path): str(content) for path, content in files.items()}


def _safe_output_name(name: str, *, default: str) -> str:
    candidate = Path(name.replace("\\", "/")).name.strip()
    if not candidate or candidate in {".", ".."}:
        return default
    return candidate


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
