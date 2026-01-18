import time
from typing import Literal, Optional
import jwt
from fastapi import HTTPException, status
from services.api.core.config import settings

Role = Literal["CUSTOMER", "OPS", "QA", "ADMIN"]

def sign_token(user_id: str, role: Role, ttl_seconds: int = 3600) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + ttl_seconds,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e
