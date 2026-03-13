import os
from typing import Dict

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from auth_service.models import (
    Credentials,
    Token,
    User,
    create_access_token,
    hash_password,
    verify_password,
)

SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "changeme-in-production")

app = FastAPI(title="Auth Service")


# Demo in-memory users
_users: Dict[str, User] = {
    "alice": User(
        username="alice",
        full_name="Alice Student",
        role="user",
        password_hash=hash_password("password"),
    ),
    "admin": User(
        username="admin",
        full_name="Admin User",
        role="admin",
        password_hash=hash_password("admin"),
    ),
}


def authenticate_user(username: str, password: str) -> User:
    user = _users.get(username)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    return user


@app.post("/auth/login", response_model=Token, tags=["auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    token = create_access_token(
        data={"sub": user.username, "role": user.role}, secret_key=SECRET_KEY
    )
    return Token(access_token=token)


@app.get("/auth/users/me", response_model=User, tags=["auth"])
async def get_me(token: str) -> User:
    """
    Simple endpoint that decodes the token and returns user info.
    Can be useful for debugging or if another service wants to validate via REST.
    """
    from auth_service.models import decode_token

    payload = decode_token(token, secret_key=SECRET_KEY)
    username = payload.get("sub")
    if not username or username not in _users:
        raise HTTPException(status_code=404, detail="User not found")
    return _users[username]


@app.get("/")
async def root():
    return {"message": "Auth Service. Use /auth/login to get a token."}

