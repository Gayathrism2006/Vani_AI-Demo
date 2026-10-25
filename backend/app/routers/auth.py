import re
import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr
from app.config import JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str

def hash_password(password: str) -> str:
    """Hashes password securely with SHA-256 + salt."""
    salt = "vani_ai_secure_salt_2026"
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

@router.post("/register")
def register(req: RegisterRequest):
    """
    Registers a new user account:
    - Validates email format, name, and password strength (min 6 chars)
    - Verifies email is not already registered
    - Hashes password securely
    - Returns JWT token and user info
    """
    email = req.email.strip().lower()
    full_name = req.full_name.strip()
    password = req.password

    if not email:
        raise HTTPException(status_code=400, detail="Email address is required.")
    if not EMAIL_REGEX.match(email):
        raise HTTPException(status_code=400, detail="Please provide a valid email address.")
    if not full_name:
        raise HTTPException(status_code=400, detail="Full name is required.")
    if len(full_name) < 2:
        raise HTTPException(status_code=400, detail="Full name must be at least 2 characters.")
    if not password:
        raise HTTPException(status_code=400, detail="Password is required.")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")

    conn = get_db()
    cursor = conn.cursor()

    # Check for existing user
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists. Please log in instead."
        )

    pwd_hash = hash_password(password)
    now = datetime.utcnow().isoformat()

    cursor.execute(
        "INSERT INTO users (email, password_hash, full_name, created_at) VALUES (?, ?, ?, ?)",
        (email, pwd_hash, full_name, now)
    )
    conn.commit()

    cursor.execute("SELECT id, email, full_name FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    token_data = {
        "sub": user["email"],
        "user_id": user["id"],
        "name": user["full_name"]
    }
    token = create_access_token(token_data)

    user_info = {
        "id": user["id"],
        "email": user["email"],
        "name": user["full_name"]
    }
    conn.close()

    return {
        "success": True,
        "token": token,
        "user": user_info,
        "message": "Account created successfully! Welcome to Vani AI."
    }

@router.post("/login")
def login(req: LoginRequest):
    """
    Authenticates an existing user:
    - Validates email and password
    - Verifies password against secure hash
    - Returns JWT token and user info
    """
    email = req.email.strip().lower()
    password = req.password

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required.")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="No account found with this email. Please click 'Create Account' to sign up."
        )

    pwd_hash = hash_password(password)
    # Check current salted hash, or fallback to legacy unsalted hash for backward compatibility
    legacy_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

    if user["password_hash"] != pwd_hash and user["password_hash"] != legacy_hash:
        conn.close()
        raise HTTPException(status_code=401, detail="Incorrect password. Please try again.")

    # Upgrade password hash to salted hash if it was legacy
    if user["password_hash"] == legacy_hash:
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pwd_hash, user["id"]))
        conn.commit()

    token_data = {
        "sub": user["email"],
        "user_id": user["id"],
        "name": user["full_name"]
    }
    token = create_access_token(token_data)

    user_info = {
        "id": user["id"],
        "email": user["email"],
        "name": user["full_name"]
    }
    conn.close()

    return {
        "success": True,
        "token": token,
        "user": user_info,
        "message": "Login successful"
    }

@router.get("/me")
def get_current_user(authorization: Optional[str] = Header(None)):
    """Verifies active JWT session."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication token required.")

    token = authorization.replace("Bearer ", "").strip()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"authenticated": True, "user": payload}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid session token.")
