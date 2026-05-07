from httpx import AsyncClient


async def check_password(password: str) -> dict:
    """Check password strength."""
    import re
    score = 0
    feedback = []
    
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Use at least 8 characters")
    
    if re.search(r"[a-z]", password) and re.search(r"[A-Z]", password):
        score += 1
    else:
        feedback.append("Add uppercase and lowercase letters")
    
    if re.search(r"\d", password):
        score += 1
    else:
        feedback.append("Add numbers")
    
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        score += 1
    else:
        feedback.append("Add special characters")
    
    return {"score": score, "strength": ["weak", "fair", "good", "strong", "very_strong"][score], "feedback": feedback}


async def hash_password(password: str, method: str = "bcrypt") -> dict:
    """Hash password securely."""
    if method == "bcrypt":
        import bcrypt
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        return {"hash": hashed, "method": "bcrypt"}
    elif method == "argon2":
        import argon2
        p = argon2.PasswordHasher()
        hashed = p.hash(password)
        return {"hash": hashed, "method": "argon2"}
    return {"error": "Unknown method"}


async def verify_hash(password: str, hash: str, method: str = "bcrypt") -> dict:
    """Verify password hash."""
    if method == "bcrypt":
        import bcrypt
        return {"valid": bcrypt.checkpw(password.encode(), hash.encode())}
    elif method == "argon2":
        import argon2
        p = argon2.PasswordHasher()
        try:
            p.verify(hash, password)
            return {"valid": True}
        except Exception:
            return {"valid": False}
    return {"error": "Unknown method"}


async def generate_token(length: int = 32) -> dict:
    """Generate secure random token."""
    import secrets
    token = secrets.token_urlsafe(length)
    return {"token": token, "length": length}


async def encrypt_data(data: str, key: str) -> dict:
    """Encrypt data with Fernet."""
    from cryptography.fernet import Fernet
    f = Fernet(key.encode())
    encrypted = f.encrypt(data.encode()).decode()
    return {"encrypted": encrypted}


async def decrypt_data(encrypted: str, key: str) -> dict:
    """Decrypt data with Fernet."""
    from cryptography.fernet import Fernet
    f = Fernet(key.encode())
    decrypted = f.decrypt(encrypted.encode()).decode()
    return {"decrypted": decrypted}