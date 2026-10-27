
import os
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from bson import ObjectId

from .database import users_collection


ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "").strip()

if len(SECRET_KEY) < 32:
    raise RuntimeError(
        "JWT_SECRET_KEY must be set in backend/.env "
        "and contain at least 32 characters."
    )

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")

    if len(password_bytes) > 72:
        raise ValueError(
            "Password cannot exceed 72 UTF-8 bytes."
        )

    return bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(
    password: str,
    hashed_password: str,
) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def signup_user(
    name: str,
    email: str,
    password: str,
):
    normalized_email = email.strip().lower()
    normalized_name = name.strip()

    if not normalized_name:
        return None

    existing_user = users_collection.find_one(
        {"email": normalized_email}
    )

    if existing_user:
        return None

    user = {
        "name": normalized_name,
        "email": normalized_email,
        "password": hash_password(password),
        "created_at": datetime.now(timezone.utc),
    }

    result = users_collection.insert_one(user)

    return {
        "id": str(result.inserted_id),
        "name": normalized_name,
        "email": normalized_email,
    }


def login_user(
    email: str,
    password: str,
):
    user = users_collection.find_one(
        {"email": email.strip().lower()}
    )

    if not user:
        return None

    if not verify_password(
        password,
        user.get("password", ""),
    ):
        return None

    token = create_access_token(str(user["_id"]))

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
        },
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
):
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = payload.get("sub")

        if not user_id or not ObjectId.is_valid(user_id):
            raise unauthorized

    except JWTError:
        raise unauthorized

    user = users_collection.find_one(
        {"_id": ObjectId(user_id)}
    )

    if not user:
        raise unauthorized

    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
    }
