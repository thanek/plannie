import os


class Settings:
    """Centralny dostęp do konfiguracji.

    Wartości oparte o zmienne środowiskowe są czytane leniwie (przy każdym
    odczycie), bo `PUBLIC_*` muszą reagować na zmianę env w trakcie działania
    (m.in. w testach przez monkeypatch).
    """

    SESSION_LIMIT = 100
    SESSION_MAX_AGE_HOURS = 24
    PURGE_INTERVAL_SECONDS = 3600
    USERNAME_COOKIE_MAX_AGE = 60 * 60 * 24 * 365

    @property
    def host(self) -> str:
        return os.getenv("HOST", "0.0.0.0")

    @property
    def port(self) -> int:
        return int(os.getenv("PORT", "8000"))

    @property
    def reload(self) -> bool:
        return os.getenv("RELOAD", "").lower() in ("1", "true")

    @property
    def public_host(self) -> str:
        return (os.getenv("PUBLIC_HOST") or "localhost").strip() or "localhost"

    @property
    def public_scheme(self) -> str:
        return (os.getenv("PUBLIC_SCHEME") or "").strip()

    @property
    def public_port(self) -> str:
        return (os.getenv("PUBLIC_PORT") or "").strip()


settings = Settings()
