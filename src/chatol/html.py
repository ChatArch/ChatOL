"""Small HTML parsers for Overleaf bootstrap pages."""

from __future__ import annotations

import html
import json
import re
from html.parser import HTMLParser
from typing import Any


class _MetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: list[dict[str, str]] = []
        self._in_script = False
        self.scripts: list[str] = []
        self._script_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "meta":
            self.meta.append({key.lower(): value or "" for key, value in attrs})
        if tag.lower() == "script":
            self._in_script = True
            self._script_chunks = []

    def handle_data(self, data: str) -> None:
        if self._in_script:
            self._script_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._in_script:
            self.scripts.append("".join(self._script_chunks))
            self._in_script = False
            self._script_chunks = []


def parse_overleaf_html(text: str) -> _MetaParser:
    """Parse only the Overleaf metadata we need."""

    parser = _MetaParser()
    parser.feed(text)
    return parser


def extract_csrf_token(text: str) -> str | None:
    """Extract a CSRF token from common Overleaf page locations."""

    parser = parse_overleaf_html(text)
    for meta in parser.meta:
        if meta.get("name", "").lower() == "ol-csrftoken" and meta.get("content"):
            return meta["content"]
    input_match = re.search(
        r'<input[^>]+name=["\']_csrf["\'][^>]+value=["\']([^"\']+)["\']',
        text,
        re.IGNORECASE,
    )
    if input_match:
        return html.unescape(input_match.group(1))
    for script in parser.scripts:
        match = re.search(r'csrfToken["\']?\s*[:=]\s*["\']([^"\']+)["\']', script)
        if match:
            return match.group(1)
    return None


def looks_like_login_page(text: str) -> bool:
    """Return true when an HTML response appears to be the login form."""

    return bool(
        re.search(r'<form[^>]+name=["\']loginForm["\']', text, re.IGNORECASE)
        or re.search(r'<input[^>]+name=["\']password["\']', text, re.IGNORECASE)
    )


def _json_from_meta_content(content: str) -> Any:
    return json.loads(html.unescape(content))


def extract_projects_payloads(text: str) -> list[Any]:
    """Return candidate project payloads from Overleaf project pages."""

    parser = parse_overleaf_html(text)
    candidates: list[str] = []

    for meta in parser.meta:
        name = meta.get("name", "")
        content = meta.get("content", "")
        if not content:
            continue
        if name in {"ol-prefetchedprojectsblob", "ol-projects"}:
            candidates.append(content)

    for meta in parser.meta:
        content = meta.get("content", "")
        if '"projects"' in html.unescape(content):
            candidates.append(content)

    payloads: list[Any] = []
    for candidate in candidates:
        try:
            payloads.append(_json_from_meta_content(candidate))
        except json.JSONDecodeError:
            continue
    return payloads
