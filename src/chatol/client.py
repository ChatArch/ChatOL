"""Native Python client for Overleaf internal workflows."""

from __future__ import annotations

import http.cookiejar
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from http.cookiejar import Cookie
from typing import Any

from chatol.errors import AuthenticationError, CompileError, ProjectNotFoundError
from chatol.html import extract_csrf_token, extract_projects_payloads, looks_like_login_page
from chatol.models import CompileOutput, CompileResult, Project

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

        url = output.url
        if result and result.clsi_server_id:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}clsiserverid={urllib.parse.quote(result.clsi_server_id)}"
        response = self._request("GET", _absolute_url(self.base_url, url))
        if not response.ok:
            raise CompileError("download_failed", f"Download failed: {response.status}")
        return response.body

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
