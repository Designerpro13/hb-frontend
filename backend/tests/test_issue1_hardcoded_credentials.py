"""
Tests for issue #1 — Hardcoded credentials and secrets in backend source.

Verifies:
- ADMIN_TOKEN, DB_PASSWORD, and DB_CONNECTION_STRING are read from environment
  variables, not hardcoded literals.
- The /health endpoint does NOT expose admin_token or db_password.
- The /api/debug endpoint does NOT expose a hardcoded_secrets block.
- The exception handler does NOT leak secrets in 500 responses.
- The app raises a clear RuntimeError when required secrets are missing.
"""
import os
import sys
import importlib
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Previously-hardcoded literal values that must never appear in source code
# or in any HTTP response.
BANNED_LITERALS = [
    "admin123456789",
    "db_password_super_secret_123",
    "mysql://admin:db_password_super_secret_123@localhost:3306/ctf_db",
]

# Environment variables used in tests — distinct from the banned literals
_TEST_ADMIN_TOKEN = "test-admin-token-for-issue1"
_TEST_DB_PASSWORD = "test-db-password-for-issue1"
_TEST_DB_CONNECTION = "mysql://admin:test-db-password-for-issue1@localhost:3306/test_db"


def _fresh_app(extra_env: dict | None = None):
    """Return a fresh TestClient by reloading app.main with the given env vars."""
    env = {
        "APP_ENV": "production",
        "ADMIN_TOKEN": _TEST_ADMIN_TOKEN,
        "DB_PASSWORD": _TEST_DB_PASSWORD,
        "DB_CONNECTION_STRING": _TEST_DB_CONNECTION,
    }
    if extra_env:
        env.update(extra_env)

    for key, value in env.items():
        os.environ[key] = value

    sys.modules.pop("app.main", None)
    from app.main import app  # noqa: PLC0415

    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# 1. Secrets must come from environment variables
# ---------------------------------------------------------------------------

class TestSecretsFromEnv:
    """Module-level constants must read from os.getenv, not from literals."""

    def test_admin_token_matches_env_var(self):
        """ADMIN_TOKEN constant must equal the value set in the environment."""
        os.environ["ADMIN_TOKEN"] = _TEST_ADMIN_TOKEN
        os.environ["DB_PASSWORD"] = _TEST_DB_PASSWORD
        os.environ["DB_CONNECTION_STRING"] = _TEST_DB_CONNECTION
        sys.modules.pop("app.main", None)
        import app.main as m  # noqa: PLC0415
        importlib.reload(m)
        assert m.ADMIN_TOKEN == _TEST_ADMIN_TOKEN, \
            "ADMIN_TOKEN must be read from the ADMIN_TOKEN env var"

    def test_db_password_matches_env_var(self):
        """DB_PASSWORD constant must equal the value set in the environment."""
        os.environ["ADMIN_TOKEN"] = _TEST_ADMIN_TOKEN
        os.environ["DB_PASSWORD"] = _TEST_DB_PASSWORD
        os.environ["DB_CONNECTION_STRING"] = _TEST_DB_CONNECTION
        sys.modules.pop("app.main", None)
        import app.main as m  # noqa: PLC0415
        importlib.reload(m)
        assert m.DB_PASSWORD == _TEST_DB_PASSWORD, \
            "DB_PASSWORD must be read from the DB_PASSWORD env var"

    def test_db_connection_string_matches_env_var(self):
        """DB_CONNECTION_STRING constant must equal the env var value."""
        os.environ["ADMIN_TOKEN"] = _TEST_ADMIN_TOKEN
        os.environ["DB_PASSWORD"] = _TEST_DB_PASSWORD
        os.environ["DB_CONNECTION_STRING"] = _TEST_DB_CONNECTION
        sys.modules.pop("app.main", None)
        import app.main as m  # noqa: PLC0415
        importlib.reload(m)
        assert m.DB_CONNECTION_STRING == _TEST_DB_CONNECTION, \
            "DB_CONNECTION_STRING must be read from the DB_CONNECTION_STRING env var"

    def test_no_banned_literal_in_admin_token(self):
        """The ADMIN_TOKEN constant must not equal the old hardcoded value."""
        os.environ["ADMIN_TOKEN"] = _TEST_ADMIN_TOKEN
        os.environ["DB_PASSWORD"] = _TEST_DB_PASSWORD
        os.environ["DB_CONNECTION_STRING"] = _TEST_DB_CONNECTION
        sys.modules.pop("app.main", None)
        import app.main as m  # noqa: PLC0415
        importlib.reload(m)
        assert m.ADMIN_TOKEN != "admin123456789", \
            "ADMIN_TOKEN must not be the old hardcoded literal"

    def test_missing_admin_token_raises(self):
        """Startup must fail with RuntimeError when ADMIN_TOKEN is absent."""
        saved = os.environ.pop("ADMIN_TOKEN", None)
        os.environ["DB_PASSWORD"] = _TEST_DB_PASSWORD
        os.environ["DB_CONNECTION_STRING"] = _TEST_DB_CONNECTION
        sys.modules.pop("app.main", None)
        try:
            # Patch load_dotenv so the .env file does not repopulate ADMIN_TOKEN.
            from unittest.mock import patch
            with patch("dotenv.load_dotenv", return_value=None):
                with pytest.raises((RuntimeError, Exception)):
                    import app.main  # noqa: PLC0415
                    importlib.reload(app.main)
        finally:
            if saved is not None:
                os.environ["ADMIN_TOKEN"] = saved

    def test_missing_db_password_raises(self):
        """Startup must fail with RuntimeError when DB_PASSWORD is absent."""
        saved = os.environ.pop("DB_PASSWORD", None)
        os.environ["ADMIN_TOKEN"] = _TEST_ADMIN_TOKEN
        os.environ["DB_CONNECTION_STRING"] = _TEST_DB_CONNECTION
        sys.modules.pop("app.main", None)
        try:
            from unittest.mock import patch
            with patch("dotenv.load_dotenv", return_value=None):
                with pytest.raises((RuntimeError, Exception)):
                    import app.main  # noqa: PLC0415
                    importlib.reload(app.main)
        finally:
            if saved is not None:
                os.environ["DB_PASSWORD"] = saved


# ---------------------------------------------------------------------------
# 2. /health must NOT expose secrets
# ---------------------------------------------------------------------------

class TestHealthEndpointNoSecrets:
    """/health must return ok=True but must not include admin_token or db_password."""

    @pytest.fixture(autouse=True)
    def client(self):
        self._client = _fresh_app()

    def test_health_returns_ok(self):
        response = self._client.get("/health")
        assert response.status_code == 200
        assert response.json().get("ok") is True

    def test_health_no_admin_token_key(self):
        response = self._client.get("/health")
        body = response.json()
        assert "admin_token" not in body, \
            "/health must not include 'admin_token' in the response"

    def test_health_no_db_password_key(self):
        response = self._client.get("/health")
        body = response.json()
        assert "db_password" not in body, \
            "/health must not include 'db_password' in the response"

    def test_health_no_banned_literal_in_body(self):
        response = self._client.get("/health")
        text = response.text
        for literal in BANNED_LITERALS:
            assert literal not in text, \
                f"/health must not contain banned literal: {literal!r}"


# ---------------------------------------------------------------------------
# 3. /api/debug must NOT expose a hardcoded_secrets block
# ---------------------------------------------------------------------------

class TestDebugEndpointNoHardcodedSecrets:
    """/api/debug must not return a hardcoded_secrets key."""

    @pytest.fixture(autouse=True)
    def client(self):
        self._client = _fresh_app()

    def test_debug_no_hardcoded_secrets_key(self):
        response = self._client.get("/api/debug")
        assert response.status_code == 200
        body = response.json()
        assert "hardcoded_secrets" not in body, \
            "/api/debug must not include a 'hardcoded_secrets' block"

    def test_debug_no_banned_literal_in_body(self):
        response = self._client.get("/api/debug")
        text = response.text
        for literal in BANNED_LITERALS:
            assert literal not in text, \
                f"/api/debug must not contain banned literal: {literal!r}"


# ---------------------------------------------------------------------------
# 4. Exception handler must not leak secrets in 500 responses
# ---------------------------------------------------------------------------

class TestExceptionHandlerNoSecretLeak:
    """500 responses must not contain secrets or stack traces."""

    def test_500_no_banned_literal(self):
        client = _fresh_app()
        from app.main import app  # noqa: PLC0415

        @app.get("/test/raise-issue1")
        async def _raise():
            raise RuntimeError("intentional: admin123456789 db_password_super_secret_123")

        c = TestClient(app, raise_server_exceptions=False)
        response = c.get("/test/raise-issue1")

        assert response.status_code == 500
        text = response.text
        for literal in BANNED_LITERALS:
            assert literal not in text, \
                f"500 response must not contain banned literal: {literal!r}"

    def test_500_has_correlation_id(self):
        client = _fresh_app()
        from app.main import app  # noqa: PLC0415

        @app.get("/test/raise-issue1b")
        async def _raise_b():
            raise ValueError("another error")

        c = TestClient(app, raise_server_exceptions=False)
        response = c.get("/test/raise-issue1b")

        assert response.status_code == 500
        body = response.json()
        assert "correlation_id" in body, "500 response must include a correlation_id"
        assert "error" in body, "500 response must include an error message"
        assert "traceback" not in body, "500 response must not include a traceback"
