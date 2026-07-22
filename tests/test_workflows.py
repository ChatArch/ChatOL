from pathlib import Path
import zipfile
from io import BytesIO

from chatenv import EnvStore, get_paths

from chatol import workflows
from chatol.config import OverleafConfig
from chatol.errors import CompileError
from chatol.models import AdminStatus, CompileOutput, CompileResult, Project, ProjectFile, UploadResult
from chatol.workflows import (
    admin_status,
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
    upload_file,
    upload_template,
    write_template,
)


class FakeClient:
    def __init__(self):
        self.projects = [Project(id="p1", name="Paper")]
        self.compile_attempts = 0

    def list_projects(self):
        return self.projects

    def get_project(self, project):
        for candidate in self.projects:
            if project in {candidate.id, candidate.name}:
                return candidate
        raise AssertionError("unexpected project")

    def compile_project(self, project_id):
        self.compile_attempts += 1
        if self.compile_attempts == 1:
            raise CompileError("too-recently-compiled")
        return CompileResult(
            status="success",
            output_files=[
                CompileOutput(path="output.pdf", url="/pdf", type="pdf"),
                CompileOutput(path="output.log", url="/log", type="log"),
            ],
        )

    def download_pdf(self, project_id):
        return b"%PDF fake"

    def download_output(self, project_id, output_type):
        return f"artifact:{output_type}".encode()

    def download_compile_output(self, output, result=None):
        return f"bundle:{output.path}".encode()

    def list_files(self, project_id):
        return [ProjectFile(path="main.tex", type="doc", id="doc1", name="main.tex")]

    def download_project_zip(self, project_id):
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("main.tex", "Hello")
            archive.writestr("refs.bib", "@book{x}")
        return buffer.getvalue()

    def upload_file(self, project_id, content, remote_path):
        return UploadResult(remote_path=remote_path, entity_id="entity1", entity_type="doc")

    def delete_file(self, project_id, remote_path):
        return ProjectFile(path=remote_path, type="doc", id="entity1", name=remote_path)

    def admin_status(self):
        return AdminStatus(available=True, authenticated=False, status_code=403, message="admin route requires admin")


class RecorderClient:
    calls = []

    @classmethod
    def from_password(cls, base_url, email, password, *, timeout=30.0):
        cls.calls.append(("password", base_url, email, password, timeout))
        return cls()

    @classmethod
    def from_session_cookie(cls, base_url, session_cookie, *, cookie_name="overleaf_session2", timeout=30.0):
        cls.calls.append(("session", base_url, session_cookie, cookie_name, timeout))
        return cls()


def test_client_from_env_loads_active_chatenv_profile(tmp_path: Path, monkeypatch):
    store = EnvStore(get_paths(tmp_path).envs_dir)
    store.save_active(
        OverleafConfig,
        {
            "OVERLEAF_SITE_URL": "https://overleaf.example.test",
            "OVERLEAF_SESSION_COOKIE": "session-from-chatenv",
            "OVERLEAF_HTTP_TIMEOUT": "12.5",
        },
    )
    RecorderClient.calls = []
    monkeypatch.setattr(workflows, "OverleafClient", RecorderClient)

    workflows.client_from_env(chatarch_home=tmp_path)

    assert RecorderClient.calls == [
        ("session", "https://overleaf.example.test", "session-from-chatenv", "overleaf_session2", 12.5)
    ]


def test_client_from_env_prefers_process_env_over_chatenv(tmp_path: Path, monkeypatch):
    store = EnvStore(get_paths(tmp_path).envs_dir)
    store.save_active(
        OverleafConfig,
        {
            "OVERLEAF_SITE_URL": "https://from-chatenv.example.test",
            "OVERLEAF_SESSION_COOKIE": "session-from-chatenv",
        },
    )
    monkeypatch.setenv("OVERLEAF_SITE_URL", "https://from-env.example.test")
    monkeypatch.setenv("OVERLEAF_SESSION_COOKIE", "session-from-env")
    RecorderClient.calls = []
    monkeypatch.setattr(workflows, "OverleafClient", RecorderClient)

    workflows.client_from_env(chatarch_home=tmp_path)

    assert RecorderClient.calls == [
        ("session", "https://from-env.example.test", "session-from-env", "overleaf_session2", 30.0)
    ]


def test_client_from_env_ignores_legacy_and_nonofficial_env_aliases(tmp_path: Path, monkeypatch):
    for name in (
        "OVERLEAF_SITE_URL",
        "OVERLEAF_ADMIN_EMAIL",
        "OVERLEAF_ADMIN_PASSWORD",
        "OVERLEAF_SESSION_COOKIE",
        "OVERLEAF_HTTP_TIMEOUT",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("CHATOL_BASE_URL", "https://legacy.example.test")
    monkeypatch.setenv("CHATOL_SESSION", "legacy-session")
    monkeypatch.setenv("OVERLEAF_BASE_URL", "https://nonofficial.example.test")
    monkeypatch.setenv("OVERLEAF_SESSION", "nonofficial-session")

    try:
        workflows.client_from_env(chatarch_home=tmp_path)
    except ValueError as exc:
        assert "OVERLEAF_SITE_URL" in str(exc)
    else:  # pragma: no cover - defensive assertion for the contract.
        raise AssertionError("legacy env aliases should not configure Overleaf clients")


def test_workflow_functions_accept_direct_client():
    client = FakeClient()

    assert list_projects(client=client)[0].name == "Paper"
    assert get_project("Paper", client=client).id == "p1"


def test_compile_project_retries_retryable_errors():
    client = FakeClient()

    project, result = compile_project("Paper", client=client, retry_delays=(0, 0), sleep=lambda _: None)

    assert project.id == "p1"
    assert result.status == "success"
    assert client.compile_attempts == 2


def test_download_workflows_write_files(tmp_path: Path):
    client = FakeClient()

    pdf_path = download_pdf("Paper", tmp_path / "paper.pdf", client=client)
    output_path = download_output("Paper", "log", tmp_path / "paper.log", client=client)

    assert pdf_path.read_bytes() == b"%PDF fake"
    assert output_path.read_bytes() == b"artifact:log"


def test_file_workflows_zip_pull_and_upload(tmp_path: Path):
    client = FakeClient()

    assert list_files("Paper", client=client)[0].path == "main.tex"
    zip_path = download_project_zip("Paper", tmp_path / "paper.zip", client=client)
    pulled = pull_project("Paper", tmp_path / "paper", client=client)
    local = tmp_path / "agent-note.tex"
    local.write_text("% agent note\n", encoding="utf-8")
    uploaded = upload_file("Paper", local, client=client)
    deleted = delete_file("Paper", "agent-note.tex", client=client)

    assert zip_path.read_bytes().startswith(b"PK")
    assert sorted(path.name for path in pulled) == ["main.tex", "refs.bib"]
    assert (tmp_path / "paper" / "main.tex").read_text(encoding="utf-8") == "Hello"
    assert uploaded.remote_path == "agent-note.tex"
    assert deleted.path == "agent-note.tex"


def test_compile_bundle_downloads_multiple_artifacts_once(tmp_path: Path):
    client = FakeClient()

    result = download_compile_bundle(
        "Paper",
        tmp_path / "bundle",
        output_types=("pdf", "log"),
        include_project_zip=True,
        client=client,
        retry_delays=(0, 0),
        sleep=lambda _: None,
    )

    assert [artifact.output_type for artifact in result.artifacts] == ["pdf", "log", "project_zip"]
    assert (tmp_path / "bundle" / "output.pdf").read_bytes() == b"bundle:output.pdf"
    assert (tmp_path / "bundle" / "output.log").read_bytes() == b"bundle:output.log"
    assert (tmp_path / "bundle" / "project.zip").read_bytes().startswith(b"PK")
    assert client.compile_attempts == 2


def test_template_workflows_write_and_upload(tmp_path: Path):
    specs = list_templates()
    names = {spec.name for spec in specs}

    assert "article-basic" in names
    written = write_template("article-basic", tmp_path / "template")
    uploaded = upload_template("Paper", tmp_path / "template", client=FakeClient())

    assert sorted(path.name for path in written) == ["main.tex", "references.bib"]
    assert (tmp_path / "template" / "main.tex").read_text(encoding="utf-8").startswith("\\documentclass")
    assert [item.remote_path for item in uploaded] == ["main.tex", "references.bib"]


def test_admin_status_is_read_only_workflow():
    status = admin_status(client=FakeClient())

    assert status.available is True
    assert status.authenticated is False


def test_pull_project_refuses_zip_slip(tmp_path: Path):
    class UnsafeZipClient(FakeClient):
        def download_project_zip(self, project_id):
            buffer = BytesIO()
            with zipfile.ZipFile(buffer, "w") as archive:
                archive.writestr("../escape.tex", "bad")
            return buffer.getvalue()

    try:
        pull_project("Paper", tmp_path / "paper", client=UnsafeZipClient())
    except ValueError as exc:
        assert "unsafe zip path" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected zip-slip protection")
