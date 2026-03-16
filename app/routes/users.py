from fastapi import APIRouter, Depends, HTTPException, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal
from app import models, auth

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------
# REGISTER
# -----------------------------
@router.post("/register")
def register(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("agent"),
    db: Session = Depends(get_db)
):
    user_exists = db.query(models.User).filter(models.User.username == username).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Utilisateur déjà existant")

    hashed_pw = auth.get_password_hash(password)
    user = models.User(username=username, hashed_password=hashed_pw, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "Utilisateur créé", "username": user.username, "role": user.role}

# -----------------------------
# LOGIN
# -----------------------------
@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Identifiants invalides"})

    # Redirection selon rôle
    response = RedirectResponse(url=f"/dashboard/{user.role}", status_code=302)
    auth.set_auth_cookie(response, user)
    return response

# -----------------------------
# LOGOUT
# -----------------------------
@router.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response
