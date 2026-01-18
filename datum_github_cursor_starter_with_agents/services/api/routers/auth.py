from fastapi import APIRouter
from pydantic import BaseModel
from services.api.core.security import sign_token

router = APIRouter()

class LoginRequest(BaseModel):
    user_id: str
    role: str

@router.post("/login")
def login(req: LoginRequest):
    # Placeholder: replace with real auth provider later
    token = sign_token(req.user_id, req.role)  # type: ignore[arg-type]
    return {"access_token": token, "token_type": "bearer"}
