"""module for hashing passwords using bcrypt."""

import bcrypt


def hash_password(pw: str) -> str:
    """Hash password menggunakan bcrypt.

    Args:
        pw: Plain text password

    Returns:
        Hashed password sebagai string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pw.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(pw: str, hashed: str) -> bool:
    """Verify password dengan hash yang tersimpan.

    Args:
        pw: Plain text password
        hashed: Hashed password dari database

    Returns:
    Args:
        pw: Plain text password
        hashed: Hashed password dari database

    Returns:
        True jika password cocok, False jika tidak
    """
    return bcrypt.checkpw(pw.encode("utf-8"), hashed.encode("utf-8"))
