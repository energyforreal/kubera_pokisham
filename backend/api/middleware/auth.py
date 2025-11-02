"""Authentication middleware for API."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import os

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None
    exp: Optional[datetime] = None


class User(BaseModel):
    """User model."""
    username: str
    email: Optional[str] = None
    disabled: bool = False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> TokenData:
    """Verify JWT token."""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        exp: datetime = payload.get("exp")
        
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        token_data = TokenData(username=username, exp=exp)
        return token_data
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")


async def get_current_user(token_data: TokenData = Depends(verify_token)) -> User:
    """Get current authenticated user."""
    # In production, fetch user from database
    # For now, return a simple user object
    user = User(username=token_data.username)
    
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user


# Optional: API Key authentication (simpler alternative)
API_KEY = os.getenv("API_KEY", "")


def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> bool:
    """Verify API key."""
    if not API_KEY:
        return True  # API key not configured, allow access
    
    token = credentials.credentials
    
    if token != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return True


