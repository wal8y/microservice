import os
from typing import Any, Dict, Optional

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer

from auth_service.models import decode_token

API_GATEWAY_PORT = int(os.getenv("API_GATEWAY_PORT", "8003"))

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
QURAN_SERVICE_URL = os.getenv("QURAN_SERVICE_URL", "http://localhost:8000")
NOTIFICATION_SERVICE_URL = os.getenv(
    "NOTIFICATION_SERVICE_URL", "http://localhost:8002"
)

AUTH_SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "changeme-in-production")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{AUTH_SERVICE_URL}/auth/login")

app = FastAPI(title="API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    # Decode token locally using shared secret (Auth service issues tokens with same key)
    payload = decode_token(token, secret_key=AUTH_SECRET_KEY)
    return payload


def require_role(user: Dict[str, Any], required_role: str) -> None:
    role = user.get("role")
    if role != required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
        )


@app.get("/")
async def root():
    return {
        "message": "API Gateway. Use /api/quran/* and /api/notifications/* (auth required)."
    }


@app.post("/api/auth/login")
async def gateway_login(request: Request):
    """
    Pass-through login endpoint that forwards credentials to the Auth service.
    """
    form = await request.form()
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{AUTH_SERVICE_URL}/auth/login", data=form)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@app.get("/api/quran/{path:path}")
async def proxy_quran(
    path: str,
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Proxy read-only Quran endpoints, enforcing authentication.
    """
    url = f"{QURAN_SERVICE_URL}/{path}"
    async with httpx.AsyncClient() as client:
        resp = await client.request(
            method=request.method,
            url=url,
            params=dict(request.query_params),
        )
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@app.api_route(
    "/api/notifications/{path:path}",
    methods=["GET", "POST"],
)
async def proxy_notifications(
    path: str,
    request: Request,
    user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Proxy notification operations, requiring 'admin' role.
    """
    require_role(user, "admin")

    url = f"{NOTIFICATION_SERVICE_URL}/{path}"
    async with httpx.AsyncClient() as client:
        if request.method == "GET":
            resp = await client.get(url, params=dict(request.query_params))
        else:
            body = await request.json()
            resp = await client.post(url, json=body)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)

