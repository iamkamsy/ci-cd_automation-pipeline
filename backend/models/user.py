from datetime import datetime, timezone


def make_user(username: str, email: str, password_hash: str) -> dict:
    return {
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc),
    }
