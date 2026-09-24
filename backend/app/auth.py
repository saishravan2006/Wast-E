"""JWT authentication, password hashing, and role-based access dependencies."""

from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_optional_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User | None:
    if token is None:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()


# Role-based dependency factories
def require_seller(user: User = Depends(get_current_user)) -> User:
    if not user.is_seller:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seller access required")
    return user


def require_buyer(user: User = Depends(get_current_user)) -> User:
    if not user.is_buyer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Buyer access required")
    return user


def require_operator(user: User = Depends(get_current_user)) -> User:
    if not user.is_operator:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operator access required")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required")
    return user


def get_user_org_id(user: User, db: Session) -> str:
    """Get the primary organisation ID for a user."""
    from app.models.organisation import OrgMembership
    membership = db.query(OrgMembership).filter(
        OrgMembership.user_id == user.id,
        OrgMembership.is_primary == True,
    ).first()
    if membership is None:
        raise HTTPException(status_code=400, detail="No organisation linked to this account")
    return membership.org_id
