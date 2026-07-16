from pathlib import Path

from chatenv import EnvStore, get_paths

from chatol import workflows
from chatol.config import OverleafConfig
from chatol.errors import CompileError
from chatol.models import CompileOutput, CompileResult, Project
from chatol.workflows import compile_project, download_output, download_pdf, get_project, list_projects


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
        return CompileResult(status="success", output_files=[CompileOutput(path="output.pdf", url="/pdf", type="pdf")])

    def download_pdf(self, project_id):
        return b"%PDF fake"

    def download_output(self, project_id, output_type):
        return f"artifact:{output_type}".encode()


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
