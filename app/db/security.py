"""密码加密和验证。

使用 bcrypt，企业级标准。
"""
from bcrypt import hashpw, gensalt, checkpw


def hash_password(password: str) -> str:
    """加密密码。"""
    # bcrypt 要求密码为 bytes
    password_bytes = password.encode("utf-8")
    salt = gensalt()
    hashed = hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码。"""
    try:
        return checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False