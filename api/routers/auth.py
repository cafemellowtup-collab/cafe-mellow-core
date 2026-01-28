"""
Authentication Router - Secure Login/Signup with JWT
Professional-grade auth for TITAN ERP
"""
import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, EmailStr

from pillars.config_vault import EffectiveSettings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/health")
async def health_check():
    """Health check for Auth service"""
    return {"ok": True, "service": "auth", "status": "healthy"}


# JWT secret - in production, use environment variable
JWT_SECRET = os.environ.get("JWT_SECRET", secrets.token_hex(32))
JWT_EXPIRY_HOURS = 24 * 7  # 7 days


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    org_name: Optional[str] = "My Organization"


class AuthResponse(BaseModel):
    ok: bool
    token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    message: str


def _hash_password(password: str, salt: str = "") -> str:
    """Hash password with salt"""
    if not salt:
        salt = secrets.token_hex(16)
    combined = f"{salt}:{password}"
    hashed = hashlib.sha256(combined.encode()).hexdigest()
    return f"{salt}:{hashed}"


def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored hash"""
    try:
        salt = stored_hash.split(":")[0]
        new_hash = _hash_password(password, salt)
        return new_hash == stored_hash
    except Exception:
        return False


def _create_token(user_id: str, email: str, role: str) -> str:
    """Create a simple JWT-like token (base64 encoded JSON with signature)"""
    import base64
    import hmac
    
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": (datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)).isoformat(),
        "iat": datetime.utcnow().isoformat()
    }
    
    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode()
    
    signature = hmac.new(
        JWT_SECRET.encode(),
        payload_b64.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"{payload_b64}.{signature}"


def _verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify token and return payload"""
    import base64
    import hmac
    
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        
        payload_b64, signature = parts
        
        expected_sig = hmac.new(
            JWT_SECRET.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_sig):
            return None
        
        payload_json = base64.urlsafe_b64decode(payload_b64.encode()).decode()
        payload = json.loads(payload_json)
        
        exp = datetime.fromisoformat(payload.get("exp", ""))
        if datetime.utcnow() > exp:
            return None
        
        return payload
    except Exception:
        return None


def _get_bq_client():
    try:
        from google.cloud import bigquery
        
        cfg = EffectiveSettings()
        key_file = getattr(cfg, "KEY_FILE", "service-key.json")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        key_path = key_file if os.path.isabs(key_file) else os.path.join(project_root, key_file)
        
        if os.path.exists(key_path):
            return bigquery.Client.from_service_account_json(key_path)
        
        project_id = getattr(cfg, "PROJECT_ID", None) or os.environ.get("PROJECT_ID")
        return bigquery.Client(project=project_id) if project_id else bigquery.Client()
    except Exception:
        return None


def _ensure_auth_table(client, cfg) -> str:
    """Ensure auth_users table exists"""
    project_id = getattr(cfg, "PROJECT_ID", "")
    dataset_id = getattr(cfg, "DATASET_ID", "")
    table_id = f"{project_id}.{dataset_id}.auth_users"
    
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS `{table_id}` (
        id STRING NOT NULL,
        name STRING NOT NULL,
        email STRING NOT NULL,
        password_hash STRING NOT NULL,
        phone STRING,
        org_id STRING NOT NULL,
        org_name STRING,
        role STRING DEFAULT 'admin',
        status STRING DEFAULT 'active',
        created_at TIMESTAMP NOT NULL,
        last_login TIMESTAMP,
        login_count INT64 DEFAULT 0
    )
    """
    try:
        client.query(create_sql).result()
    except Exception:
        pass
    
    return table_id


@router.post("/signup")
async def signup(req: SignupRequest) -> AuthResponse:
    """Register a new user"""
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    try:
        table_id = _ensure_auth_table(client, cfg)
        
        # Check if email exists
        check_query = f"""
        SELECT COUNT(*) as cnt
        FROM `{table_id}`
        WHERE LOWER(email) = LOWER('{req.email}')
        """
        result = list(client.query(check_query).result())
        if result and result[0].cnt > 0:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        user_id = f"user_{int(datetime.now().timestamp() * 1000)}"
        org_id = f"org_{int(datetime.now().timestamp() * 1000)}"
        password_hash = _hash_password(req.password)
        
        # Escape single quotes in strings
        name_safe = req.name.replace("'", "''")
        org_name_safe = (req.org_name or "My Organization").replace("'", "''")
        phone_safe = (req.phone or "").replace("'", "''")
        
        insert_sql = f"""
        INSERT INTO `{table_id}`
        (id, name, email, password_hash, phone, org_id, org_name, role, status, created_at, login_count)
        VALUES (
            '{user_id}',
            '{name_safe}',
            '{req.email}',
            '{password_hash}',
            '{phone_safe}',
            '{org_id}',
            '{org_name_safe}',
            'admin',
            'active',
            CURRENT_TIMESTAMP(),
            0
        )
        """
        client.query(insert_sql).result()
        
        # Generate token
        token = _create_token(user_id, req.email, "admin")
        
        return AuthResponse(
            ok=True,
            token=token,
            user={
                "id": user_id,
                "name": req.name,
                "email": req.email,
                "org_id": org_id,
                "org_name": req.org_name or "My Organization",
                "role": "admin"
            },
            message="Account created successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login")
async def login(req: LoginRequest) -> AuthResponse:
    """Authenticate user and return token"""
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    try:
        table_id = _ensure_auth_table(client, cfg)
        
        # Find user by email
        query = f"""
        SELECT id, name, email, password_hash, org_id, org_name, role, status
        FROM `{table_id}`
        WHERE LOWER(email) = LOWER('{req.email}')
        LIMIT 1
        """
        result = list(client.query(query).result())
        
        if not result:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user = result[0]
        
        if user.status != "active":
            raise HTTPException(status_code=401, detail="Account is inactive")
        
        if not _verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Update last login
        update_sql = f"""
        UPDATE `{table_id}`
        SET last_login = CURRENT_TIMESTAMP(), login_count = login_count + 1
        WHERE id = '{user.id}'
        """
        client.query(update_sql).result()
        
        # Generate token
        token = _create_token(user.id, user.email, user.role)
        
        return AuthResponse(
            ok=True,
            token=token,
            user={
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "org_id": user.org_id,
                "org_name": user.org_name,
                "role": user.role
            },
            message="Login successful"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me")
async def get_current_user(authorization: str = Header(None)) -> Dict[str, Any]:
    """Get current user from token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    token = authorization.replace("Bearer ", "")
    payload = _verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    cfg = EffectiveSettings()
    client = _get_bq_client()
    
    if not client:
        # Return from token if DB unavailable
        return {
            "ok": True,
            "user": {
                "id": payload.get("user_id"),
                "email": payload.get("email"),
                "role": payload.get("role")
            }
        }
    
    try:
        table_id = _ensure_auth_table(client, cfg)
        
        query = f"""
        SELECT id, name, email, org_id, org_name, role, status
        FROM `{table_id}`
        WHERE id = '{payload.get("user_id")}'
        LIMIT 1
        """
        result = list(client.query(query).result())
        
        if not result:
            raise HTTPException(status_code=401, detail="User not found")
        
        user = result[0]
        
        return {
            "ok": True,
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "org_id": user.org_id,
                "org_name": user.org_name,
                "role": user.role
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logout")
async def logout() -> Dict[str, Any]:
    """Logout (client should discard token)"""
    return {"ok": True, "message": "Logged out successfully"}


@router.post("/verify")
async def verify_token(authorization: str = Header(None)) -> Dict[str, Any]:
    """Verify if token is valid"""
    if not authorization:
        return {"ok": False, "valid": False}
    
    token = authorization.replace("Bearer ", "")
    payload = _verify_token(token)
    
    if not payload:
        return {"ok": False, "valid": False}
    
    return {
        "ok": True,
        "valid": True,
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
        "role": payload.get("role"),
        "expires": payload.get("exp")
    }
