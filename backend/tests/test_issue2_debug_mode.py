"""
Tests for issue #2 — Debug mode and verbose exception responses.

Verifies:
- The FastAPI app does NOT expose stack traces, DB connection strings, or
  secrets in HTTP 500 responses.
- The response body contains only a generic error message and a correlation ID.
- The app's debug flag is controlled by APP_ENV (False when not "development").
"""
import os
import re
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client(app_env: str = "production") -> TestClient:
    """Return a TestClient with APP_ENV set to the given value."""
    os.environ["APP_ENV"] = app_env
    # Re-import after env change so the debug flag is re-evaluated.
    import importlib
    import sys

    # Remove cached module so the app is re-created with the new env var.
    sys.modules.pop("app.main", None)
    from app.main import app  # noqa: PLC0415
    importlib.reload(app.router.__class__)  # not needed but explicit
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture()
def production_client():
    """TestClient with APP_ENV=production (the safe default)."""
    os.environ["APP_ENV"] = "production"
    # Force a fresh import each time.
    import sys
    sys.modules.pop("app.main", None)
    from app.main import app  # noqa: PLC0415
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# 1. Exception handler must NOT leak internals
# ---------------------------------------------------------------------------

class TestSafeExceptionHandler:
    """The exception handler must return only a generic message + correlation_id."""

    def test_500_body_has_no_traceback(self, production_client: TestClient):
        """Stack trace must never appear in the response body."""
        # /api/search with a crafted payload that won't cause a Python exception
        # in this app, so we trigger the handler via a route that raises.
        # We use the deserialization endpoint which is benign but we need an
        # actual 500 — monkeypatch a route instead.
        from app.main import app
        from fastapi import Request
        from fastapi.responses import JSONResponse

        @app.get("/test/raise")
        async def _raise():
            raise RuntimeError("intentional test error with secret: admin123456789")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test/raise")

        assert response.status_code == 500
        body = response.json()

        # Must NOT contain traceback key
        assert "traceback" not in body, "Response must not include a traceback"

        # Must NOT contain the raw exception message (which includes secrets)
        response_text = response.text
        assert "admin123456789" not in response_text, \
            "Admin token must not appear in the HTTP response"
        assert "db_password_super_secret_123" not in response_text, \
            "DB password must not appear in the HTTP response"
        assert "mysql://" not in response_text, \
            "DB connection string must not appear in the HTTP response"
        assert "intentional test error" not in response_text, \
            "Raw exception message must not appear in the HTTP response"

    def test_500_body_has_generic_error_and_correlation_id(self, production_client: TestClient):
        """Response must contain 'error' and 'correlation_id' keys only."""
        from app.main import app
        from fastapi import Request

        @app.get("/test/raise2")
        async def _raise2():
            raise ValueError("another test error")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test/raise2")

        assert response.status_code == 500
        body = response.json()

        assert "error" in body, "Response body must include an 'error' key"
        assert "correlation_id" in body, "Response body must include a 'correlation_id' key"

        # Correlation ID should look like a UUID
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        )
        assert uuid_pattern.match(body["correlation_id"]), \
            f"correlation_id '{body['correlation_id']}' is not a valid UUID"

    def test_500_body_has_no_request_path(self, production_client: TestClient):
        """request_path must not be included in the error response."""
        from app.main import app

        @app.get("/test/raise3")
        async def _raise3():
            raise Exception("path leak test")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test/raise3")

        assert response.status_code == 500
        body = response.json()
        assert "request_path" not in body, \
            "request_path must not be included in the error response"

    def test_500_body_has_no_db_connection_key(self, production_client: TestClient):
        """db_connection must not be included in the error response."""
        from app.main import app

        @app.get("/test/raise4")
        async def _raise4():
            raise Exception("db leak test")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test/raise4")

        assert response.status_code == 500
        body = response.json()
        assert "db_connection" not in body, \
            "db_connection must not be included in the error response"

    def test_500_body_has_no_admin_token_key(self, production_client: TestClient):
        """admin_token must not be included in the error response."""
        from app.main import app

        @app.get("/test/raise5")
        async def _raise5():
            raise Exception("token leak test")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test/raise5")

        assert response.status_code == 500
        body = response.json()
        assert "admin_token" not in body, \
            "admin_token must not be included in the error response"


# ---------------------------------------------------------------------------
# 2. Debug flag must respect APP_ENV
# ---------------------------------------------------------------------------

class TestDebugFlagEnvControl:
    """The app's debug flag must be False outside development."""

    def test_debug_false_in_production(self):
        """APP_ENV=production → app.debug must be False."""
        import sys
        os.environ["APP_ENV"] = "production"
        sys.modules.pop("app.main", None)
        from app.main import app  # noqa: PLC0415
        assert app.debug is False, \
            "app.debug must be False when APP_ENV=production"

    def test_debug_false_when_env_unset(self):
        """When APP_ENV is explicitly set to anything other than 'development',
        app.debug must be False.  (The .env file in this repo sets development,
        so we test the explicit non-development value instead of relying on
        the absence of APP_ENV, which load_dotenv() would repopulate.)"""
        import sys
        os.environ["APP_ENV"] = "staging"
        sys.modules.pop("app.main", None)
        from app.main import app  # noqa: PLC0415
        assert app.debug is False, \
            "app.debug must be False when APP_ENV is not 'development' (e.g. staging)"

    def test_debug_true_in_development(self):
        """APP_ENV=development → app.debug may be True (local dev only)."""
        import sys
        os.environ["APP_ENV"] = "development"
        sys.modules.pop("app.main", None)
        from app.main import app  # noqa: PLC0415
        assert app.debug is True, \
            "app.debug should be True in development to aid local debugging"
