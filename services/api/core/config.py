import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    env: str = os.getenv("DATUM_ENV", "dev")
    jwt_secret: str = os.getenv("DATUM_JWT_SECRET", "dev-secret-change-me")

settings = Settings()
