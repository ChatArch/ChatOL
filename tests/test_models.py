import pytest

from chatol.client import HttpResponse, OverleafClient
from chatol.errors import CompileError
from chatol.models import CompileOutput, CompileResult, Project


def test_project_to_dict_omits_private_user_metadata_by_default():
    project = Project(
        id="p1",
        name="Paper",
        last_updated_by={"email": "person@example.test"},
        owner={"email": "owner@example.test"},
    )

    public = project.to_dict()
    private = project.to_dict(include_private=True)

    assert "last_updated_by" not in public
    assert "owner" not in public
    assert private["last_updated_by"] == {"email": "person@example.test"}
    assert private["owner"] == {"email": "owner@example.test"}


def test_compile_result_to_dict_omits_internal_output_urls_by_default():
    result = CompileResult(
        status="success",
        output_files=[CompileOutput(path="output.pdf", url="/project/p1/output/output.pdf", type="pdf")],
    )

    output = result.to_dict()["output_files"][0]

    assert "url" not in output


def test_download_compile_output_rejects_cross_origin_urls():
    client = OverleafClient("https://overleaf.example.test")
    output = CompileOutput(path="output.pdf", url="https://attacker.example.test/output.pdf", type="pdf")

    with pytest.raises(CompileError, match="cross-origin"):
        client.download_compile_output(output)


def test_download_compile_output_allows_same_origin_absolute_urls(monkeypatch):
    client = OverleafClient("https://overleaf.example.test")
    output = CompileOutput(path="output.pdf", url="https://overleaf.example.test/output/output.pdf", type="pdf")
    result = CompileResult(status="success", output_files=[output], clsi_server_id="server 1")
    seen = {}

    def fake_request(method, path_or_url, **kwargs):
        seen["method"] = method
        seen["url"] = path_or_url
        return HttpResponse(status=200, headers={}, body=b"%PDF", url=path_or_url)

    monkeypatch.setattr(client, "_request", fake_request)

    assert client.download_compile_output(output, result) == b"%PDF"
    assert seen == {
        "method": "GET",
        "url": "https://overleaf.example.test/output/output.pdf?clsiserverid=server%201",
    }
