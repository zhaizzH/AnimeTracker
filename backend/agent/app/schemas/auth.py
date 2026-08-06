from pydantic import BaseModel
from typing import Literal


class UserInfo(BaseModel):
    user_id: int
    username: str
    role: Literal["USER", "ADMIN"]
    token: str = ""


class AuthResult(BaseModel):
    ok: bool
    user: UserInfo | None = None
    error: str | None = None
