from pathlib import Path

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
