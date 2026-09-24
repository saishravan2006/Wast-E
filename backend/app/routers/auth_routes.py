"""Authentication routes — register, login, current user."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import hash_password, verify_password, create_access_token, get_current_user, get_user_org_id
from app.models.user import User
from app.models.organisation import Organisation, OrgMembership
from app.schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        phone=req.phone,
        is_seller=req.is_seller,
        is_buyer=req.is_buyer,
    )
    db.add(user)
    db.flush()

    # Create organisation if name provided
    org_id = None
    org_name = None
    if req.org_name:
        org = Organisation(name=req.org_name, org_type=req.org_type)
        db.add(org)
        db.flush()
        membership = OrgMembership(user_id=user.id, org_id=org.id, role="owner", is_primary=True)
        db.add(membership)
        org_id = org.id
        org_name = org.name

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id, email=user.email, full_name=user.full_name,
        phone=user.phone, is_seller=user.is_seller, is_buyer=user.is_buyer,
        is_operator=user.is_operator, is_admin=user.is_admin, is_demo=user.is_demo,
        org_id=org_id, org_name=org_name, created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token({"sub": user.id})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org_id = None
    org_name = None
    try:
        org_id = get_user_org_id(user, db)
        org = db.query(Organisation).filter(Organisation.id == org_id).first()
        if org:
            org_name = org.name
    except Exception:
        pass

    return UserResponse(
        id=user.id, email=user.email, full_name=user.full_name,
        phone=user.phone, is_seller=user.is_seller, is_buyer=user.is_buyer,
        is_operator=user.is_operator, is_admin=user.is_admin, is_demo=user.is_demo,
        org_id=org_id, org_name=org_name, created_at=user.created_at,
    )
