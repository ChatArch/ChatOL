"Typed environment configuration for Overleaf."

from chatenv import BaseEnvConfig, EnvField


class OverleafConfig(BaseEnvConfig):
    "Overleaf ChatEnv configuration."

    _title = "Overleaf Configuration"
    _aliases = ["overleaf"]
    _storage_dir = "Overleaf"

    @classmethod
    def test(cls) -> None:
        """Validate schema registration without external side effects."""

        print(f"Testing {cls._title}...")
        print("Schema loaded; live Overleaf checks are done by `oleaf doctor`.")

    OVERLEAF_SITE_URL = EnvField(
        "OVERLEAF_SITE_URL",
        desc="Overleaf instance site URL",
        is_sensitive=False,
    )
    OVERLEAF_ADMIN_EMAIL = EnvField(
        "OVERLEAF_ADMIN_EMAIL",
        desc="Overleaf admin or login email",
        is_sensitive=True,
    )
    OVERLEAF_ADMIN_PASSWORD = EnvField(
        "OVERLEAF_ADMIN_PASSWORD",
        desc="Overleaf admin or login password",
        is_sensitive=True,
    )
    OVERLEAF_SESSION_COOKIE = EnvField(
        "OVERLEAF_SESSION_COOKIE",
        desc="Overleaf session cookie value",
        is_sensitive=True,
    )
    OVERLEAF_SESSION_COOKIE_NAME = EnvField(
        "OVERLEAF_SESSION_COOKIE_NAME",
        desc="Overleaf session cookie name",
        is_sensitive=False,
    )
    OVERLEAF_HTTP_TIMEOUT = EnvField(
        "OVERLEAF_HTTP_TIMEOUT",
        desc="HTTP timeout in seconds",
        is_sensitive=False,
    )


__all__ = ["OverleafConfig"]
