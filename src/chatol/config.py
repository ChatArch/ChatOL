"Typed environment configuration for ChatOL."

from chatenv import BaseEnvConfig, EnvField


class ChatolConfig(BaseEnvConfig):
    "ChatOL ChatEnv configuration."

    _title = "ChatOL Configuration"
    _aliases = ["chatol"]
    _storage_dir = "Chatol"

    @classmethod
    def test(cls) -> None:
        """Validate schema registration without external side effects."""

        print(f"Testing {cls._title}...")
        print("Schema loaded; live Overleaf checks are done by `chatol doctor`.")

    CHATOL_BASE_URL = EnvField(
        "CHATOL_BASE_URL",
        desc="Overleaf instance base URL",
        is_sensitive=False,
    )
    CHATOL_EMAIL = EnvField(
        "CHATOL_EMAIL",
        desc="Overleaf login email",
        is_sensitive=True,
    )
    CHATOL_PASSWORD = EnvField(
        "CHATOL_PASSWORD",
        desc="Overleaf login password",
        is_sensitive=True,
    )
    CHATOL_SESSION = EnvField(
        "CHATOL_SESSION",
        desc="Overleaf session cookie value",
        is_sensitive=True,
    )
    CHATOL_COOKIE_NAME = EnvField(
        "CHATOL_COOKIE_NAME",
        desc="Overleaf session cookie name",
        is_sensitive=False,
    )
    CHATOL_TIMEOUT = EnvField(
        "CHATOL_TIMEOUT",
        desc="HTTP timeout in seconds",
        is_sensitive=False,
    )


__all__ = ["ChatolConfig"]
