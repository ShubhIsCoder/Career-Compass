from __future__ import annotations

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from app.config import settings


class AuthService:
    def __init__(self) -> None:
        self.serializer = URLSafeTimedSerializer(settings.secret_key, salt="career-compass-auth")

    @staticmethod
    def hash_password(password: str) -> str:
        return generate_password_hash(password)

    @staticmethod
    def verify_password(password_hash: str, password: str) -> bool:
        return check_password_hash(password_hash, password)

    def issue_token(self, user_id: int) -> str:
        return self.serializer.dumps({"user_id": user_id})

    def parse_token(self, token: str) -> int | None:
        try:
            payload = self.serializer.loads(token, max_age=settings.token_ttl_seconds)
        except (BadSignature, SignatureExpired):
            return None
        user_id = payload.get("user_id")
        return int(user_id) if user_id is not None else None
