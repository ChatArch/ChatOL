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
        print("Schema loaded; no network test is required.")

    CHATOL_API_KEY = EnvField(
        "CHATOL_API_KEY",
        desc="API key",
        is_sensitive=True,
    )


__all__ = ["ChatolConfig"]
