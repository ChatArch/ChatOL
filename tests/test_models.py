import json

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


def test_client_lists_project_files_from_entities(monkeypatch):
    client = OverleafClient("https://overleaf.example.test")

    def fake_request(method, path_or_url, **kwargs):
        assert method == "GET"
        assert path_or_url == "/project/p1/entities"
        return HttpResponse(
            status=200,
            headers={},
            body=b'{"entities":[{"path":"/main.tex","type":"doc","_id":"doc1"}]}',
            url="https://overleaf.example.test/project/p1/entities",
        )

    monkeypatch.setattr(client, "_request", fake_request)

    files = client.list_files("p1")
    assert files[0].path == "main.tex"
    assert files[0].id == "doc1"


def test_client_upload_file_uses_root_folder_metadata(monkeypatch):
    client = OverleafClient("https://overleaf.example.test", csrf_token="csrf")
    calls = []

    def fake_request(method, path_or_url, **kwargs):
        calls.append((method, path_or_url, kwargs))
        if method == "GET":
            html = '<meta name="ol-project" content="{&quot;rootFolder&quot;:[{&quot;_id&quot;:&quot;root1&quot;}]}" />'
            return HttpResponse(status=200, headers={}, body=html.encode(), url="https://overleaf.example.test/project/p1")
        assert method == "POST"
        assert path_or_url == "/project/p1/upload?folder_id=root1"
        assert b'name="targetFolderId"' in kwargs["body"]
        assert b"root1" in kwargs["body"]
        assert b'filename="agent-note.tex"' in kwargs["body"]
        return HttpResponse(
            status=200,
            headers={},
            body=b'{"success":true,"entity_id":"doc2","entity_type":"doc"}',
            url="https://overleaf.example.test/project/p1/upload",
        )

    monkeypatch.setattr(client, "_request", fake_request)

    result = client.upload_file("p1", b"% note\n", "agent-note.tex")
    assert result.entity_id == "doc2"
    assert calls[0][0] == "GET"
    assert calls[1][0] == "POST"


def test_client_upload_file_computes_root_folder_when_metadata_missing(monkeypatch):
    project_id = "6a57be6360d5eb57666020f4"
    client = OverleafClient("https://overleaf.example.test", csrf_token="csrf")

    def fake_request(method, path_or_url, **kwargs):
        if method == "GET":
            return HttpResponse(status=200, headers={}, body=b"<html></html>", url="https://overleaf.example.test/project/p1")
        assert method == "POST"
        assert path_or_url == f"/project/{project_id}/upload?folder_id=6a57be6360d5eb57666020f3"
        assert b"6a57be6360d5eb57666020f3" in kwargs["body"]
        return HttpResponse(
            status=200,
            headers={},
            body=b'{"success":true,"entity_id":"doc2","entity_type":"doc"}',
            url="https://overleaf.example.test/project/p1/upload",
        )

    monkeypatch.setattr(client, "_request", fake_request)

    result = client.upload_file(project_id, b"% note\n", "agent-note.tex")
    assert result.entity_id == "doc2"


def test_client_upload_file_reads_root_folder_from_socket_payload(monkeypatch):
    client = OverleafClient("https://overleaf.example.test", csrf_token="csrf")
    socket_project = {
        "name": "joinProjectResponse",
        "args": [{"project": {"rootFolder": [{"_id": "root1", "docs": [], "fileRefs": []}]}}],
    }

    def fake_request(method, path_or_url, **kwargs):
        if method == "GET" and path_or_url == "/project/p1":
            return HttpResponse(status=200, headers={}, body=b"<html></html>", url="https://overleaf.example.test/project/p1")
        if method == "GET" and path_or_url.startswith("/socket.io/1/?"):
            return HttpResponse(status=200, headers={}, body=b"sid123:60:60:xhr-polling", url="https://overleaf.example.test/socket.io/1/")
        if method == "GET" and path_or_url.startswith("/socket.io/1/xhr-polling/sid123"):
            body = f"5:::{json.dumps(socket_project)}".encode()
            return HttpResponse(status=200, headers={}, body=body, url="https://overleaf.example.test/socket.io/1/xhr-polling/sid123")
        if method == "POST" and path_or_url.startswith("/socket.io/1/xhr-polling/sid123"):
            return HttpResponse(status=200, headers={}, body=b"", url="https://overleaf.example.test/socket.io/1/xhr-polling/sid123")
        assert method == "POST"
        assert path_or_url == "/project/p1/upload?folder_id=root1"
        assert b"root1" in kwargs["body"]
        return HttpResponse(
            status=200,
            headers={},
            body=b'{"success":true,"entity_id":"doc2","entity_type":"doc"}',
            url="https://overleaf.example.test/project/p1/upload",
        )

    monkeypatch.setattr(client, "_request", fake_request)

    result = client.upload_file("p1", b"% note\n", "agent-note.tex")
    assert result.entity_id == "doc2"


def test_client_delete_file_requires_entity_id(monkeypatch):
    client = OverleafClient("https://overleaf.example.test", csrf_token="csrf")
    calls = []

    def fake_request(method, path_or_url, **kwargs):
        calls.append((method, path_or_url))
        if method == "GET":
            return HttpResponse(
                status=200,
                headers={},
                body=b'{"entities":[{"path":"/agent-note.tex","type":"doc","_id":"doc2"}]}',
                url="https://overleaf.example.test/project/p1/entities",
            )
        assert method == "DELETE"
        assert path_or_url == "/project/p1/doc/doc2"
        return HttpResponse(status=204, headers={}, body=b"", url="https://overleaf.example.test/project/p1/doc/doc2")

    monkeypatch.setattr(client, "_request", fake_request)

    deleted = client.delete_file("p1", "agent-note.tex")
    assert deleted.id == "doc2"
    assert calls == [("GET", "/project/p1/entities"), ("DELETE", "/project/p1/doc/doc2")]


def test_client_delete_file_falls_back_to_project_metadata_for_id(monkeypatch):
    client = OverleafClient("https://overleaf.example.test", csrf_token="csrf")
    calls = []

    def fake_request(method, path_or_url, **kwargs):
        calls.append((method, path_or_url))
        if path_or_url == "/project/p1/entities":
            return HttpResponse(
                status=200,
                headers={},
                body=b'{"entities":[{"path":"/agent-note.tex","type":"doc"}]}',
                url="https://overleaf.example.test/project/p1/entities",
            )
        if path_or_url == "/project/p1":
            html = (
                '<meta name="ol-project" '
                'content="{&quot;rootFolder&quot;:[{&quot;_id&quot;:&quot;root1&quot;,&quot;docs&quot;:'
                '[{&quot;_id&quot;:&quot;doc2&quot;,&quot;name&quot;:&quot;agent-note.tex&quot;}]}]}" />'
            )
            return HttpResponse(status=200, headers={}, body=html.encode(), url="https://overleaf.example.test/project/p1")
        assert method == "DELETE"
        assert path_or_url == "/project/p1/doc/doc2"
        return HttpResponse(status=204, headers={}, body=b"", url="https://overleaf.example.test/project/p1/doc/doc2")

    monkeypatch.setattr(client, "_request", fake_request)

    deleted = client.delete_file("p1", "agent-note.tex")
    assert deleted.id == "doc2"
    assert calls == [("GET", "/project/p1/entities"), ("GET", "/project/p1"), ("DELETE", "/project/p1/doc/doc2")]
