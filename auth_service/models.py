from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel


class User(BaseModel):
    username: str
    full_name: str
    role: str  # e.g. "user", "admin"
    password_hash: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Credentials(BaseModel):
    username: str
    password: str


def _simple_hash(password: str) -> str:
    # NOTE: For demo only. In production, use bcrypt/argon2.
    import hashlib

    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain_password: str, password_hash: str) -> bool:
    return _simple_hash(plain_password) == password_hash


def hash_password(plain_password: str) -> str:
    return _simple_hash(plain_password)


def create_access_token(
    data: Dict[str, str],
    secret_key: str,
    algorithm: str = "HS256",
    expires_minutes: int = 60,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt


def decode_token(token: str, secret_key: str, algorithm: str = "HS256") -> Dict:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

