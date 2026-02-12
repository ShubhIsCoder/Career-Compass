from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    tier: str = Field(default="free", pattern="^(free|pro|enterprise)$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=2000)
    session_id: int | None = None


class ChatResponse(BaseModel):
    reply: str
    provider: str
    model: str
    session_id: int


class AuthResponse(BaseModel):
    access_token: str
    user_id: int
    tier: str
