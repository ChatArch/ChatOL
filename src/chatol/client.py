"""Native Python client for Overleaf internal workflows."""

from __future__ import annotations

import http.cookiejar
import html
import json
import mimetypes
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from http.cookiejar import Cookie
from typing import Any

from chatol.errors import AuthenticationError, CompileError, FileOperationError, ProjectNotFoundError, UnsupportedRouteError
from chatol.html import extract_csrf_token, extract_projects_payloads, looks_like_login_page, parse_overleaf_html
from chatol.models import AdminStatus, CompileOutput, CompileResult, Project, ProjectFile, UploadResult

USER_AGENT = "ChatOL/0.1 (+https://github.com/ChatArch/ChatOL)"
DEFAULT_COOKIE_NAME = "overleaf_session2"


@dataclass(frozen=True)
class HttpResponse:
    """Small response object used by OverleafClient."""

    status: int
    headers: dict[str, str]
    body: bytes
    url: str

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        return json.loads(self.text())


class OverleafClient:
    """Callable Python API for Overleaf project workflows.

    The CLI in `chatol.cli` should stay a thin layer over this class or over
    functions in `chatol.workflows`.
    """

    def __init__(
        self,
        base_url: str,
        *,
        cookie_jar: http.cookiejar.CookieJar | None = None,
        csrf_token: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.cookie_jar = cookie_jar or http.cookiejar.CookieJar()
        self.csrf_token = csrf_token
        self.timeout = timeout
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie_jar))

    @classmethod
    def from_password(
        cls,
        base_url: str,
        email: str,
        password: str,
        *,
        timeout: float = 30.0,
    ) -> "OverleafClient":
        """Create a client by submitting Overleaf's password login form."""

        client = cls(base_url, timeout=timeout)
        login_page = client._request("GET", "/login")
        if not login_page.ok:
            raise AuthenticationError(f"Failed to fetch login page: {login_page.status}")
        csrf = extract_csrf_token(login_page.text())
        if not csrf:
            raise AuthenticationError("Could not find CSRF token on login page")

        body = urllib.parse.urlencode({"_csrf": csrf, "email": email, "password": password}).encode()
        response = client._request(
            "POST",
            "/login",
            body=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response_text = response.text()
        if looks_like_login_page(response_text):
            raise AuthenticationError("Password login failed or still returned login page")

        project_page = response if "/project" in response.url else client._request("GET", "/project")
        if not project_page.ok:
            raise AuthenticationError(f"Failed to fetch projects page after login: {project_page.status}")
        if looks_like_login_page(project_page.text()):
            raise AuthenticationError("Password login failed; project page returned login form")
        project_csrf = extract_csrf_token(project_page.text())
        if not project_csrf:
            raise AuthenticationError("Could not find CSRF token after login")
        client.csrf_token = project_csrf
        return client

    @classmethod
    def from_session_cookie(
        cls,
        base_url: str,
        session_cookie: str,
        *,
        cookie_name: str = DEFAULT_COOKIE_NAME,
        timeout: float = 30.0,
    ) -> "OverleafClient":
        """Create a client from an existing Overleaf session cookie."""

        client = cls(base_url, timeout=timeout)
        client.cookie_jar.set_cookie(_make_cookie(base_url, cookie_name, session_cookie))
        project_page = client._request("GET", "/project")
        if not project_page.ok:
            raise AuthenticationError(f"Failed to fetch project page: {project_page.status}")
        if looks_like_login_page(project_page.text()):
            raise AuthenticationError("Authentication required; session cookie may be expired")
        csrf = extract_csrf_token(project_page.text())
        if not csrf:
            raise AuthenticationError("Could not find CSRF token for session")
        client.csrf_token = csrf
        return client

    def session_cookie(self, cookie_name: str = DEFAULT_COOKIE_NAME) -> str | None:
        """Return the current session cookie value when present."""

        for cookie in self.cookie_jar:
            if cookie.name == cookie_name:
                return cookie.value
        return None

    def list_projects(self) -> list[Project]:
        """List projects visible to the current user."""

        response = self._request("GET", "/project")
        if not response.ok:
            raise AuthenticationError(f"Failed to fetch projects: {response.status}")
        projects: list[Project] = []
        for payload in extract_projects_payloads(response.text()):
            raw_projects = payload.get("projects", payload) if isinstance(payload, dict) else payload
            if not isinstance(raw_projects, list):
                continue
            projects = [Project.from_overleaf(item) for item in raw_projects if isinstance(item, dict)]
            if projects:
                break
        return [project for project in projects if not project.archived and not project.trashed]

    def get_project(self, project: str) -> Project:
        """Resolve a project by id or exact name."""

        projects = self.list_projects()
        for candidate in projects:
            if candidate.id == project or candidate.name == project:
                return candidate
        raise ProjectNotFoundError(f"Project not found: {project}")

    def list_files(self, project_id: str) -> list[ProjectFile]:
        """List file-like entities in a project when the Overleaf route is available."""

        response = self._request("GET", f"/project/{project_id}/entities")
        if response.status == 404:
            raise UnsupportedRouteError("The Overleaf /entities route is not available on this instance")
        if not response.ok:
            raise FileOperationError(f"Failed to list project files: {response.status}")
        payload = response.json()
        raw_items = payload.get("entities", payload) if isinstance(payload, dict) else payload
        if not isinstance(raw_items, list):
            raise FileOperationError("Unexpected project entities response")
        return [ProjectFile.from_overleaf(item) for item in raw_items if isinstance(item, dict)]

    def download_project_zip(self, project_id: str) -> bytes:
        """Download a project archive as zip bytes."""

        response = self._request("GET", f"/project/{project_id}/download/zip")
        if response.status == 404:
            raise UnsupportedRouteError("The project zip download route is not available on this instance")
        if not response.ok:
            raise FileOperationError(f"Failed to download project zip: {response.status}")
        return response.body

    def upload_file(self, project_id: str, content: bytes, remote_path: str) -> UploadResult:
        """Upload one file to the project root.

        Nested remote paths require folder discovery/creation. ChatOL keeps this
        first mutation slice root-only until folder sync is implemented and live
        practiced.
        """

        normalized_path = remote_path.strip().replace("\\", "/").lstrip("/")
        if not normalized_path or normalized_path.endswith("/"):
            raise FileOperationError("remote_path must name a file")
        if "/" in normalized_path:
            raise UnsupportedRouteError("Nested upload paths are not implemented yet; upload to the project root first")

        root_folder_id = self._root_folder_id(project_id)
        mime_type = mimetypes.guess_type(normalized_path)[0] or "application/octet-stream"
        body, content_type = _multipart_form_data(
            {
                "targetFolderId": root_folder_id,
                "name": normalized_path,
                "type": mime_type,
            },
            file_field="qqfile",
            file_name=normalized_path,
            file_content=content,
            file_content_type=mime_type,
        )
        response = self._request(
            "POST",
            f"/project/{project_id}/upload?folder_id={urllib.parse.quote(root_folder_id)}",
            body=body,
            headers={"Content-Type": content_type},
        )
        if not response.ok:
            raise FileOperationError(f"Failed to upload file: {response.status} {response.text()[:200]}")
        try:
            payload = response.json()
        except json.JSONDecodeError:
            payload = {}
        if isinstance(payload, dict) and payload.get("success") is False:
            raise FileOperationError(f"Failed to upload file: {payload.get('error') or 'unknown error'}")
        return UploadResult(
            remote_path=normalized_path,
            entity_id=payload.get("entity_id") if isinstance(payload, dict) else None,
            entity_type=payload.get("entity_type") if isinstance(payload, dict) else None,
        )

    def delete_file(self, project_id: str, remote_path: str) -> ProjectFile:
        """Delete one project file by path after resolving it through `/entities`."""

        normalized_path = remote_path.strip().replace("\\", "/").lstrip("/")
        for entity in self.list_files(project_id):
            if entity.path.lstrip("/") != normalized_path:
                continue
            if not entity.id:
                entity = self._find_project_file(project_id, normalized_path) or entity
            if not entity.id:
                raise FileOperationError(f"Entity has no id and cannot be deleted: {remote_path}")
            if entity.type not in {"doc", "file"}:
                raise FileOperationError(f"Refusing to delete unsupported entity type: {entity.type}")
            response = self._request("DELETE", f"/project/{project_id}/{entity.type}/{urllib.parse.quote(entity.id)}")
            if not response.ok:
                raise FileOperationError(f"Failed to delete file: {response.status}")
            return entity
        raise FileOperationError(f"File not found: {remote_path}")

    def admin_status(self) -> AdminStatus:
        """Probe the admin entrypoint without mutating users or projects."""

        response = self._request("GET", "/admin")
        text = response.text()
        if response.status == 404:
            return AdminStatus(False, False, response.status, "admin route not found")
        if response.status in {401, 403} or looks_like_login_page(text):
            return AdminStatus(True, False, response.status, "admin route requires an authenticated admin session")
        if response.ok:
            return AdminStatus(True, True, response.status, "admin route is reachable")
        return AdminStatus(True, False, response.status, f"admin route returned HTTP {response.status}")

    def compile_project(self, project_id: str) -> CompileResult:
        """Trigger Overleaf compilation for a project."""

        response = self._request_json(
            "POST",
            f"/project/{project_id}/compile",
            {
                "rootDoc_id": None,
                "draft": False,
                "check": "silent",
                "incrementalCompilesEnabled": True,
            },
        )
        if not response.ok:
            raise CompileError("http_error", f"Failed to compile project: {response.status}")
        data = response.json()
        status = str(data.get("status") or "unknown")
        outputs = [CompileOutput.from_overleaf(item) for item in data.get("outputFiles", []) if isinstance(item, dict)]
        result = CompileResult(
            status=status,
            output_files=outputs,
            compile_group=data.get("compileGroup"),
            clsi_server_id=data.get("clsiServerId"),
        )
        if status != "success":
            raise CompileError(status)
        return result

    def compile_project_by_name(self, project: str) -> tuple[Project, CompileResult]:
        """Resolve a project and compile it."""

        resolved = self.get_project(project)
        return resolved, self.compile_project(resolved.id)

    def download_pdf(self, project_id: str) -> bytes:
        """Compile a project and download its main PDF."""

        result = self.compile_project(project_id)
        pdf = result.pdf_output()
        if not pdf:
            raise CompileError("no_pdf", "No PDF output found")
        return self.download_compile_output(pdf, result)

    def download_output(self, project_id: str, output_type: str) -> bytes:
        """Compile a project and download one output artifact."""

        result = self.compile_project(project_id)
        output = result.find_output(output_type)
        if not output:
            raise CompileError("output_not_found", f"No output found for {output_type}")
        return self.download_compile_output(output, result)

    def download_compile_output(self, output: CompileOutput, result: CompileResult | None = None) -> bytes:
        """Download a compile output returned by `compile_project`."""

        url = _safe_output_url(self.base_url, output.url)
        if result and result.clsi_server_id:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}clsiserverid={urllib.parse.quote(result.clsi_server_id)}"
        response = self._request("GET", url)
        if not response.ok:
            raise CompileError("download_failed", f"Download failed: {response.status}")
        return response.body

    def _root_folder_id(self, project_id: str) -> str:
        """Resolve the root folder ID from the project page bootstrap metadata."""

        root_item = self._root_folder_item(project_id)
        if root_item and root_item.get("_id"):
            return str(root_item["_id"])
        computed = _compute_root_folder_id(project_id)
        if computed:
            return computed
        raise UnsupportedRouteError("Could not discover root folder ID from project metadata")

    def _root_folder_item(self, project_id: str) -> dict[str, Any] | None:
        """Return the project root folder object from bootstrap metadata or socket payload."""

        root_item = self._root_folder_item_from_html(project_id)
        if root_item:
            return root_item
        return self._root_folder_item_from_socket(project_id)

    def _root_folder_item_from_html(self, project_id: str) -> dict[str, Any] | None:
        """Return the project root folder object from bootstrap metadata."""

        response = self._request("GET", f"/project/{project_id}")
        if response.status == 404:
            raise UnsupportedRouteError("Project info page is not available for root folder discovery")
        if not response.ok:
            raise FileOperationError(f"Failed to fetch project page: {response.status}")
        parser = parse_overleaf_html(response.text())
        candidates = []
        for meta in parser.meta:
            content = meta.get("content", "")
            name = meta.get("name", "").lower()
            if content and (name == "ol-project" or "rootFolder" in html.unescape(content)):
                candidates.append(content)
        for candidate in candidates:
            try:
                payload = json.loads(html.unescape(candidate))
            except json.JSONDecodeError:
                continue
            root = payload.get("rootFolder") if isinstance(payload, dict) else None
            root_item = root[0] if isinstance(root, list) and root else root if isinstance(root, dict) else None
            if isinstance(root_item, dict):
                return root_item
        return None

    def _root_folder_item_from_socket(self, project_id: str) -> dict[str, Any] | None:
        """Fetch the project tree from Overleaf's Socket.IO join payload."""

        sid: str | None = None
        try:
            handshake = self._request("GET", f"/socket.io/1/?projectId={urllib.parse.quote(project_id)}&t={int(time.time() * 1000)}")
            if not handshake.ok:
                return None
            sid = handshake.text().strip().split(":", 1)[0]
            if not sid:
                return None
            for _ in range(6):
                poll_path = f"/socket.io/1/xhr-polling/{urllib.parse.quote(sid)}?projectId={urllib.parse.quote(project_id)}&t={int(time.time() * 1000)}"
                poll = self._request("GET", poll_path)
                if not poll.ok:
                    return None
                for packet in _decode_socket_io_payload(poll.text()):
                    project = _socket_project(packet)
                    if project:
                        root = project.get("rootFolder") if isinstance(project, dict) else None
                        root_item = root[0] if isinstance(root, list) and root else root if isinstance(root, dict) else None
                        if isinstance(root_item, dict):
                            return root_item
                    if packet.startswith("2::"):
                        self._request(
                            "POST",
                            poll_path,
                            body=b"2::",
                            headers={"Content-Type": "text/plain;charset=UTF-8"},
                        )
        except Exception:
            return None
        finally:
            if sid:
                close_path = f"/socket.io/1/xhr-polling/{urllib.parse.quote(sid)}?projectId={urllib.parse.quote(project_id)}&t={int(time.time() * 1000)}"
                try:
                    self._request(
                        "POST",
                        close_path,
                        body=b"0::",
                        headers={"Content-Type": "text/plain;charset=UTF-8"},
                    )
                except Exception:
                    pass
        return None

    def _find_project_file(self, project_id: str, remote_path: str) -> ProjectFile | None:
        """Find a doc/file id in the project metadata tree."""

        root_item = self._root_folder_item(project_id)
        if not root_item:
            return None
        normalized_path = remote_path.strip().replace("\\", "/").lstrip("/")

        def walk(folder: dict[str, Any], prefix: str = "") -> ProjectFile | None:
            for key, entity_type in (("docs", "doc"), ("fileRefs", "file")):
                for item in folder.get(key) or []:
                    if not isinstance(item, dict):
                        continue
                    name = str(item.get("name") or "")
                    path = f"{prefix}/{name}" if prefix else name
                    if path == normalized_path and item.get("_id"):
                        return ProjectFile(path=path, type=entity_type, id=str(item["_id"]), name=name)
            for child in folder.get("folders") or []:
                if not isinstance(child, dict):
                    continue
                name = str(child.get("name") or "")
                path = f"{prefix}/{name}" if prefix else name
                found = walk(child, path)
                if found:
                    return found
            return None

        return walk(root_item)

    def _request_json(self, method: str, path_or_url: str, payload: dict[str, Any]) -> HttpResponse:
        body = json.dumps(payload).encode("utf-8")
        return self._request(method, path_or_url, body=body, headers={"Content-Type": "application/json"})

    def _request(
        self,
        method: str,
        path_or_url: str,
        *,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> HttpResponse:
        url = _absolute_url(self.base_url, path_or_url)
        request_headers = {"User-Agent": USER_AGENT, **(headers or {})}
        if self.csrf_token:
            request_headers.setdefault("X-Csrf-Token", self.csrf_token)
        req = urllib.request.Request(url, data=body, method=method, headers=request_headers)
        try:
            with self._opener.open(req, timeout=self.timeout) as response:
                return HttpResponse(
                    status=response.status,
                    headers=dict(response.headers.items()),
                    body=response.read(),
                    url=response.geturl(),
                )
        except urllib.error.HTTPError as exc:
            return HttpResponse(
                status=exc.code,
                headers=dict(exc.headers.items()),
                body=exc.read(),
                url=exc.geturl(),
            )


def _absolute_url(base_url: str, path_or_url: str) -> str:
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url
    return urllib.parse.urljoin(base_url.rstrip("/") + "/", path_or_url.lstrip("/"))


def _safe_output_url(base_url: str, path_or_url: str) -> str:
    """Resolve an artifact URL and reject cross-origin downloads."""

    resolved = _absolute_url(base_url, path_or_url)
    base_parts = urllib.parse.urlparse(base_url)
    output_parts = urllib.parse.urlparse(resolved)
    if (output_parts.scheme, output_parts.netloc) != (base_parts.scheme, base_parts.netloc):
        raise CompileError("unsafe_output_url", "Refusing to download a cross-origin compile output")
    return resolved


def _multipart_form_data(
    fields: dict[str, str],
    *,
    file_field: str,
    file_name: str,
    file_content: bytes,
    file_content_type: str,
) -> tuple[bytes, str]:
    boundary = f"----chatol-{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                str(value).encode("utf-8"),
                b"\r\n",
            ]
        )
    chunks.extend(
        [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{file_field}"; filename="{file_name}"\r\n'.encode(),
            f"Content-Type: {file_content_type}\r\n\r\n".encode(),
            file_content,
            b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ]
    )
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def _compute_root_folder_id(project_id: str) -> str | None:
    """Infer the root folder ObjectID used by older Overleaf CE projects."""

    if len(project_id) != 24 or any(char not in "0123456789abcdefABCDEF" for char in project_id):
        return None
    prefix = project_id[:16]
    counter = int(project_id[16:], 16)
    if counter <= 0:
        return None
    return f"{prefix}{counter - 1:08x}"


def _decode_socket_io_payload(payload: str) -> list[str]:
    """Decode Socket.IO 0.9 packets, including length-framed payloads."""

    if not payload:
        return []
    if not payload.startswith("\ufffd"):
        return [payload]
    packets: list[str] = []
    index = 0
    while index < len(payload):
        if payload[index] != "\ufffd":
            break
        index += 1
        length_text = ""
        while index < len(payload) and payload[index] != "\ufffd":
            length_text += payload[index]
            index += 1
        if index >= len(payload) or payload[index] != "\ufffd":
            break
        index += 1
        try:
            packet_length = int(length_text)
        except ValueError:
            break
        packets.append(payload[index : index + packet_length])
        index += packet_length
    return packets


def _socket_project(packet: str) -> dict[str, Any] | None:
    if not packet.startswith("5:::"):
        return None
    try:
        payload = json.loads(packet[4:])
    except json.JSONDecodeError:
        return None
    if payload.get("name") != "joinProjectResponse":
        return None
    args = payload.get("args") or []
    if not args or not isinstance(args[0], dict):
        return None
    project = args[0].get("project")
    return project if isinstance(project, dict) else None


def _make_cookie(base_url: str, name: str, value: str) -> Cookie:
    parsed = urllib.parse.urlparse(base_url)
    return Cookie(
        version=0,
        name=name,
        value=value,
        port=None,
        port_specified=False,
        domain=parsed.hostname or "localhost",
        domain_specified=False,
        domain_initial_dot=False,
        path="/",
        path_specified=True,
        secure=parsed.scheme == "https",
        expires=None,
        discard=True,
        comment=None,
        comment_url=None,
        rest={},
        rfc2109=False,
    )
