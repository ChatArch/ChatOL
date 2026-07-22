"""ChatOL package."""

from chatol.client import OverleafClient
from chatol.models import (
    AdminStatus,
    CompileBundleResult,
    CompileOutput,
    CompileResult,
    DownloadedArtifact,
    Project,
    ProjectFile,
    TemplateSpec,
    UploadResult,
)

__all__ = [
    "AdminStatus",
    "CompileBundleResult",
    "CompileOutput",
    "CompileResult",
    "DownloadedArtifact",
    "OverleafClient",
    "Project",
    "ProjectFile",
    "TemplateSpec",
    "UploadResult",
    "__version__",
]

__version__ = "0.1.1"
