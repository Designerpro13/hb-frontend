import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Deque

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

load_dotenv()


class ItemIn(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=2000)


class ItemOut(ItemIn):
    id: int


class LoginIn(BaseModel):
    token: str = Field(min_length=16, max_length=512)


def get_allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
    return [x.strip() for x in raw.split(",") if x.strip()]


def get_trusted_hosts() -> list[str]:
    raw = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1")
    return [x.strip() for x in raw.split(",") if x.strip()]


def get_rate_limit() -> int:
    return int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))


def get_api_token() -> str:
    token = os.getenv("API_TOKEN", "")
    if not token:
        raise RuntimeError("API_TOKEN is required")
    return token


@asynccontextmanager
async def lifespan(_: FastAPI):
    app.state.items = {}
    app.state.next_id = 1
    app.state.rate_buckets = defaultdict(deque)
    yield


app = FastAPI(title="Secure CRUD API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=get_trusted_hosts())


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; base-uri 'self'"
    return response


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    bucket: Deque[float] = app.state.rate_buckets[ip]
    max_per_minute = get_rate_limit()

    while bucket and now - bucket[0] > 60:
        bucket.popleft()

    if len(bucket) >= max_per_minute:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded"},
        )

    bucket.append(now)
    return await call_next(request)


def require_auth(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    bearer = auth_header.removeprefix("Bearer ").strip()
    if bearer != get_api_token():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@app.get("/health")
def health_check():
    return {"ok": True, "env": os.getenv("APP_ENV", "development")}


@app.post("/api/login")
def login(payload: LoginIn):
    if payload.token != get_api_token():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"access_token": payload.token, "token_type": "bearer"}


@app.get("/api/items", response_model=list[ItemOut], dependencies=[Depends(require_auth)])
def list_items():
    return list(app.state.items.values())


@app.post("/api/items", response_model=ItemOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_auth)])
def create_item(payload: ItemIn):
    item = ItemOut(id=app.state.next_id, title=payload.title.strip(), description=payload.description.strip())
    app.state.items[item.id] = item
    app.state.next_id += 1
    return item


@app.put("/api/items/{item_id}", response_model=ItemOut, dependencies=[Depends(require_auth)])
def update_item(item_id: int, payload: ItemIn):
    if item_id not in app.state.items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    item = ItemOut(id=item_id, title=payload.title.strip(), description=payload.description.strip())
    app.state.items[item_id] = item
    return item


@app.delete("/api/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_auth)])
def delete_item(item_id: int):
    if item_id not in app.state.items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    del app.state.items[item_id]
    return None
