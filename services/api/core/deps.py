from fastapi import Depends, Header, HTTPException, status
from services.api.core.security import verify_token

def get_auth(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    return verify_token(token)

def require_role(*roles: str):
    def _inner(auth: dict = Depends(get_auth)) -> dict:
        if auth.get("role") not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return auth
    return _inner
