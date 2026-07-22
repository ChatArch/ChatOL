"""Data models returned by the ChatOL Python API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Project:
    """A project visible to the current Overleaf session."""

    id: str
    name: str
    last_updated: Any = None
    last_updated_by: Any = None
    owner: Any = None
    archived: bool | None = None
    trashed: bool | None = None

    @classmethod
    def from_overleaf(cls, payload: dict[str, Any]) -> "Project":
        """Normalize a project object from Overleaf's page metadata."""

        return cls(
            id=str(payload.get("id") or payload.get("_id") or ""),
            name=str(payload.get("name") or ""),
            last_updated=payload.get("lastUpdated"),
            last_updated_by=payload.get("lastUpdatedBy"),
            owner=payload.get("owner"),
            archived=payload.get("archived"),
            trashed=payload.get("trashed"),
        )

    def to_dict(self, *, include_private: bool = False) -> dict[str, Any]:
        """Return a JSON-serializable project representation.

        Owner and updater metadata can contain user IDs or emails, so CLI JSON
        omits them by default. Python callers can opt in explicitly.
        """

        data: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "last_updated": self.last_updated,
            "archived": self.archived,
            "trashed": self.trashed,
        }
        if include_private:
            data["last_updated_by"] = self.last_updated_by
            data["owner"] = self.owner
        return data


@dataclass(frozen=True)
class ProjectFile:
    """A file-like entity in an Overleaf project."""

    path: str
    type: str
    id: str | None = None
    name: str | None = None

    @classmethod
    def from_overleaf(cls, payload: dict[str, Any]) -> "ProjectFile":
        """Normalize one item from Overleaf's `/entities` response."""

        raw_path = str(payload.get("path") or payload.get("name") or "")
        path = raw_path.lstrip("/")
        name = str(payload.get("name") or path.rsplit("/", 1)[-1] or "")
        return cls(
            path=path,
            type=str(payload.get("type") or payload.get("entityType") or "file"),
            id=payload.get("id") or payload.get("_id") or payload.get("entity_id"),
            name=name,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable file representation."""

        data: dict[str, Any] = {"path": self.path, "type": self.type, "name": self.name}
        if self.id:
            data["id"] = self.id
        return data


@dataclass(frozen=True)
class UploadResult:
    """Result returned after uploading one local file."""

    remote_path: str
    entity_id: str | None = None
    entity_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "remote_path": self.remote_path,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
        }


@dataclass(frozen=True)
class CompileOutput:
    """A single file produced by an Overleaf compile."""

    path: str
    url: str
    type: str | None = None
    build: str | None = None

    @classmethod
    def from_overleaf(cls, payload: dict[str, Any]) -> "CompileOutput":
        """Normalize an output file object from Overleaf compile JSON."""

        return cls(
            path=str(payload.get("path") or payload.get("name") or ""),
            url=str(payload.get("url") or ""),
            type=payload.get("type"),
            build=payload.get("build"),
        )

    def to_dict(self, *, include_url: bool = False) -> dict[str, Any]:
        """Return a safe JSON representation.

        URLs are internal build-output links, so they are excluded unless a
        caller explicitly opts in.
        """

        data: dict[str, Any] = {"path": self.path, "type": self.type}
        if include_url:
            data["url"] = self.url
        return data


@dataclass(frozen=True)
class CompileResult:
    """Normalized compile result."""

    status: str
    output_files: list[CompileOutput] = field(default_factory=list)
    compile_group: str | None = None
    clsi_server_id: str | None = None

    def pdf_output(self) -> CompileOutput | None:
        """Return the main PDF output when present."""

        for output in self.output_files:
            if output.path == "output.pdf":
                return output
        for output in self.output_files:
            if output.type == "pdf":
                return output
        return None

    def find_output(self, output_type: str) -> CompileOutput | None:
        """Find an output by extension, path, or reported type."""

        normalized = output_type.strip().lstrip(".").lower()
        for output in self.output_files:
            path = output.path.lower()
            if output.type == normalized or path == normalized or path.endswith(f".{normalized}"):
                return output
        return None

    def to_dict(self, *, include_urls: bool = False) -> dict[str, Any]:
        """Return a JSON-serializable result safe for CLI output."""

        return {
            "status": self.status,
            "compile_group": self.compile_group,
            "output_files": [output.to_dict(include_url=include_urls) for output in self.output_files],
        }
