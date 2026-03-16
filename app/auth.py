from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, Request, status, Response
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app import models

# -----------------------------
# CONFIGURATION
# -----------------------------
SECRET_KEY = "secret_key_super_secure"   # ⚠️ à mettre dans .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -----------------------------
# DATABASE SESSION
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------
# PASSWORD HASHING
# -----------------------------
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# -----------------------------
# JWT CREATION
# -----------------------------
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# -----------------------------
# JWT DECODING
# -----------------------------
def get_current_user(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise HTTPException(status_code=401, detail="Token invalide")

        user = db.query(models.User).filter(models.User.username == username).first()
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur introuvable")

        return user   # ← retourne l'objet User
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")


# -----------------------------
# AUTH VIA COOKIE
# -----------------------------
def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")

    return get_current_user(token, db)   # ← retourne User

def set_auth_cookie(response: Response, user):
    token = create_access_token({"sub": user.username, "id": user.id, "role": user.role})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,       # ⚠️ activer en prod HTTPS
        samesite="Lax",
        max_age=3600
    )

# -----------------------------
# ROLE-BASED ACCESS CONTROL
# -----------------------------
def require_role(roles: list):
    def wrapper(current_user: models.User = Depends(get_current_user_from_cookie)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé : rôle insuffisant"
            )
        return current_user
    return wrapper

