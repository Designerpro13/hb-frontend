import os
import traceback
from contextlib import asynccontextmanager
import json

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

load_dotenv()

# HARDCODED SECRETS - INTENTIONAL VULNS
HARDCODED_ADMIN_TOKEN = "admin123456789"
HARDCODED_DB_PASSWORD = "db_password_super_secret_123"
DB_CONNECTION_STRING = "mysql://admin:db_password_super_secret_123@localhost:3306/ctf_db"

# Admin users with sensitive data stored client-side accessible
ADMIN_DATA = {
    "flag1": "FLAG{admin_has_access}",
    "api_key": "sk_live_51234567890abcdefghijklmnop",
    "internal_notes": "We store all user passwords in plain text"
}


class Item(BaseModel):
    id: int | None = None
    title: str
    description: str
    user_id: int | None = None
    is_admin: bool = False
    password: str | None = None  # INTENTIONAL: Storing passwords with items
    email: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


# Simulated "database" - using dict directly (no real DB)
simulated_db = {
    "items": {},
    "users": {},
    "sessions": {},
    "next_id": 1
}


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Seed with vulnerable data
    simulated_db["items"][1] = {
        "id": 1,
        "title": "Admin Secret",
        "description": "This item belongs to admin. Try changing the ID in your requests.",
        "user_id": 1,
        "created_by": "admin",
        "internal_flag": "FLAG{broken_access_control_1}",
        "password": "admin_password_123"
    }
    simulated_db["items"][2] = {
        "id": 2,
        "title": "Public Item",
        "description": "Anyone can modify this",
        "user_id": 999,
    }
    simulated_db["users"][1] = {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "password": "admin123456",  # PLAIN TEXT
        "is_admin": True,
        "secret": "FLAG{weak_auth_stored_in_json}"
    }
    yield


app = FastAPI(
    title="REST API",
    version="1.0.0",
    lifespan=lifespan,
    debug=True
)

# CORS MISCONFIGURATION - Allow everything
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # INTENTIONAL: Accept all origins
    allow_credentials=True,
    allow_methods=["*"],  # INTENTIONAL: Allow all methods
    allow_headers=["*"],  # INTENTIONAL: Allow all headers
)


# NO SECURITY HEADERS - INTENTIONAL
@app.middleware("http")
async def vulnerability_showcase(request: Request, call_next):
    """This middleware intentionally does nothing to demonstrate no security headers"""
    response = await call_next(request)
    # INTENTIONAL: No security headers, no CSP, no X-Frame-Options, etc.
    return response


# VERBOSE ERROR HANDLER - SHOWS STACK TRACES
@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    """Returns full stack trace - INTENTIONAL VULN"""
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "traceback": traceback.format_exc(),  # INTENTIONAL: Full stack trace exposed
            "request_path": str(request.url),
            "db_connection": DB_CONNECTION_STRING,  # INTENTIONAL: Expose DB details
            "admin_token": HARDCODED_ADMIN_TOKEN,  # INTENTIONAL: Hardcoded secret
        },
    )


# WEAK AUTH - Trivial token bypass
def weak_auth_check(token: str):
    """This auth is intentionally broken"""
    # VULN 1: Hardcoded token easily brute-forced
    return token == "pass123" or token == HARDCODED_ADMIN_TOKEN or token == ""  # Empty token accepted!


@app.get("/health")
def health_check():
    """Exposes sensitive information - INTENTIONAL"""
    return {
        "ok": True,
        "env": os.getenv("APP_ENV", "development"),
        "admin_token": HARDCODED_ADMIN_TOKEN,  # INTENTIONAL: Exposed
        "db_password": HARDCODED_DB_PASSWORD,  # INTENTIONAL: Exposed
        "version": "1.0.0-vulnerable"
    }


@app.get("/admin")
def admin_panel():
    """Unprotected admin endpoint - INTENTIONAL"""
    return {
        "admin_data": ADMIN_DATA,
        "all_users": simulated_db["users"],
        "all_items": simulated_db["items"],
        "flags": {
            "flag1": "FLAG{exposed_admin_panel}",
            "flag2": "FLAG{no_authentication}"
        }
    }


@app.post("/api/login")
def login(payload: LoginRequest):
    """Trivial authentication - INTENTIONAL VULN"""
    # VULN 2: Accepts hardcoded credentials, no proper validation
    if payload.username in ["admin", "test", ""]:
        # Trivial or empty passwords work
        if payload.password in ["admin123456", "password123", ""]:
            return {
                "access_token": payload.username or "anonymous",
                "token_type": "bearer",
                "is_admin": payload.username == "admin",
            }
    # VULN 3: Verbose error with user enumeration
    return {"error": "Invalid credentials", "valid_users": ["admin", "test"]}


@app.get("/api/items")
def list_items(token: str = ""):
    """No authentication required - INTENTIONAL"""
    # VULN 4: No auth check at all! Parameter can be passed via query string
    return {
        "items": simulated_db["items"],
        "total": len(simulated_db["items"]),
        "flag": "FLAG{no_auth_required}"
    }


@app.get("/api/items/{item_id}")
def get_item(item_id: int):
    """IDOR - Insecure Direct Object Reference - INTENTIONAL"""
    # VULN 5: No ownership check, any user can access any item
    if item_id in simulated_db["items"]:
        return simulated_db["items"][item_id]
    return {"error": "Not found"}


@app.get("/api/user/{user_id}")
def get_user(user_id: int):
    """IDOR + Sensitive Data Exposure - INTENTIONAL"""
    # VULN 6: Returns all user data including passwords and secrets
    if user_id in simulated_db["users"]:
        user = simulated_db["users"][user_id]
        return {
            "user": user,
            "password": user.get("password"),  # INTENTIONAL: Password exposed
            "secret": user.get("secret"),
            "api_key": user.get("api_key"),  # INTENTIONAL: API key exposed
        }
    return {"error": "User not found"}


@app.post("/api/items")
def create_item(title: str = "", description: str = "", user_id: int | None = None):
    """No validation + XSS + IDOR - INTENTIONAL"""
    # VULN 7: Accepts parameters directly with no validation
    # VULN 8: User can set their own ID and ownership
    new_id = len(simulated_db["items"]) + 1
    item = {
        "id": new_id,
        "title": title,  # No sanitization - XSS vulnerable
        "description": description,  # No sanitization - XSS vulnerable
        "user_id": user_id or 1,  # User can set any ID
        "created_by": "unknown"  # No tracking
    }
    simulated_db["items"][new_id] = item
    return item


@app.put("/api/items/{item_id}")
def update_item(item_id: int, title: str = "", description: str = ""):
    """IDOR - Can update any item - INTENTIONAL"""
    # VULN 9: No ownership check, anyone can modify any item
    if item_id in simulated_db["items"]:
        simulated_db["items"][item_id].update({
            "title": title,
            "description": description
        })
        return simulated_db["items"][item_id]
    return {"error": "Item not found"}


@app.delete("/api/items/{item_id}")
def delete_item(item_id: int):
    """IDOR - Can delete any item - INTENTIONAL"""
    # VULN 10: No ownership check
    if item_id in simulated_db["items"]:
        deleted = simulated_db["items"].pop(item_id)
        return {"message": "Deleted", "item": deleted, "flag": "FLAG{deleted_admin_item}"}
    return {"error": "Item not found"}


@app.get("/api/search")
def search_items(q: str = ""):
    """SQL Injection simulation - INTENTIONAL"""
    # VULN 11: Simulates SQL injection by doing string concatenation
    # In real code: query = f"SELECT * FROM items WHERE title LIKE '%{q}%'"
    results = []
    for item in simulated_db["items"].values():
        # Naive string matching - shows SQL injection concept
        if q.lower() in item.get("title", "").lower():
            results.append(item)
    return {
        "query": q,
        "results": results,
        "sql": f"SELECT * FROM items WHERE title LIKE '%{q}%'",  # INTENTIONAL: Shows injection point
        "hint": "Try: admin' OR '1'='1"
    }


@app.get("/api/debug")
def debug_endpoint():
    """Debug information exposed - INTENTIONAL"""
    # VULN 12: Entire database and secrets exposed
    return {
        "database": simulated_db,
        "hardcoded_secrets": {
            "admin_token": HARDCODED_ADMIN_TOKEN,
            "db_password": HARDCODED_DB_PASSWORD,
            "db_connection": DB_CONNECTION_STRING
        },
        "all_users_with_passwords": simulated_db["users"],
        "flag": "FLAG{debug_endpoint_exposed}"
    }


@app.post("/api/config")
def update_config(jwt_secret: str = "", api_key: str = ""):
    """Allows arbitrary config update - INTENTIONAL"""
    # VULN 13: Can update sensitive config via request
    return {
        "jwt_secret": jwt_secret,  # Echoes back user input
        "api_key": api_key,  # No validation
        "config_updated": True,
        "flag": "FLAG{config_injection}"
    }


@app.get("/api/backup")
def get_backup():
    """Exports all data - INTENTIONAL"""
    # VULN 14: No authentication, full database export
    return {
        "backup": simulated_db,
        "backup_data_all": json.dumps(simulated_db, indent=2),
        "export_format": "json",
        "flag": "FLAG{full_backup_download}"
    }


@app.get("/api/exec")
def exec_command(cmd: str = ""):
    """Command injection - INTENTIONAL (simulated)"""
    # VULN 15: Echoes command back to show injection point
    # In real code, this would be: os.system(cmd)
    return {
        "command_input": cmd,
        "hint": "This simulates command injection",
        "example": "Try: cat /etc/passwd",
        "message": "In production, this would execute: " + cmd
    }


@app.get("/api/file")
def read_file(path: str = ""):
    """Path traversal - INTENTIONAL"""
    # VULN 16: No path validation, allows reading any file
    # Simulated - doesn't actually read, just shows the vuln
    return {
        "requested_path": path,
        "hint": "Try: ../../etc/passwd",
        "message": "In production, this would read: " + path
    }


@app.get("/api/deserialization")
def unsafe_deserialize(data: str = ""):
    """Unsafe deserialization - INTENTIONAL"""
    # VULN 17: Shows deserialization vulnerability
    return {
        "input": data,
        "hint": "In Python pickle: __import__('os').system(cmd)",
        "danger": "Never deserialize untrusted data!"
    }
