from datetime import datetime
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app import models, auth
from app.utils.logs import log_action   # ← ajout important

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = "app/uploads/factures"


# --- CRÉATION D’UNE DÉPENSE ---
@router.post("/create")
def create_depense(
    description: str = Form(...),
    montant: float = Form(...),
    budget_id: int = Form(...),
    facture: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(auth.require_role(["agent"]))
):
    ext = facture.filename.split(".")[-1].lower()
    if ext not in ["pdf", "jpg", "jpeg", "png"]:
        raise HTTPException(status_code=400, detail="Format de fichier non autorisé")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, facture.filename)

    with open(file_path, "wb") as f:
        f.write(facture.file.read())

    depense = models.Depense(
        description=description,
        montant=montant,
        budget_id=budget_id,
        user_id=current_user.id,
        statut="en_attente"
    )
    db.add(depense)
    db.commit()
    db.refresh(depense)

    facture_obj = models.Facture(
        fichier=file_path,
        type_fichier=ext,
        depense_id=depense.id
    )
    db.add(facture_obj)
    db.commit()

    # Journaliser
    log_action(db, current_user.id, "création dépense", "Depense", depense.id)

    return RedirectResponse(url="/dashboard", status_code=302)

@router.get("/create")
def depense_form(request: Request, current_user = Depends(auth.require_role(["agent"]))):
    return templates.TemplateResponse("depenses_form.html", {
        "request": request,
        "user": current_user
    })
# --- VALIDATION PAR LE CONTRÔLEUR ---
from fastapi.responses import RedirectResponse

def redirect_after_action(current_user):
    if current_user.role == "agent":
        return "/dashboard/agent"
    elif current_user.role == "controleur":
        return "/dashboard/controleur"
    elif current_user.role == "admin":
        return "/dashboard/depenses"
    return "/dashboard"


# --- VALIDATION PAR LE CONTRÔLEUR / ADMIN ---
@router.post("/valider/{depense_id}")
def valider_depense(
    depense_id: int,
    commentaire: str = Form(""),
    db: Session = Depends(get_db),
    current_user = Depends(auth.require_role(["controleur", "admin"]))
):
    depense = db.query(models.Depense).filter(models.Depense.id == depense_id).first()
    if not depense:
        raise HTTPException(status_code=404, detail="Dépense introuvable")

    # Distinction des rôles
    if current_user.role == "controleur":
        depense.statut = "validé_controleur"
        depense.commentaire_controleur = commentaire

    elif current_user.role == "admin":
        depense.statut = "approuvé_admin"
        depense.commentaire_admin = commentaire

    depense.date_validation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db.commit()
    db.refresh(depense)

    # Journaliser
    log_action(db, current_user.id, "validation dépense", "Depense", depense.id)

    # Redirection vers le dashboard du rôle connecté
    return RedirectResponse(url=redirect_after_action(current_user), status_code=302)



# --- REJET PAR LE CONTRÔLEUR / ADMIN ---
@router.post("/rejeter/{depense_id}")
def rejeter_depense(
    depense_id: int,
    commentaire: str = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(auth.require_role(["controleur", "admin"]))
):
    depense = db.query(models.Depense).filter(models.Depense.id == depense_id).first()
    if not depense:
        raise HTTPException(status_code=404, detail="Dépense introuvable")

    if current_user.role == "controleur":
        depense.statut = "rejeté_controleur"
        depense.commentaire_controleur = commentaire

    elif current_user.role == "admin":
        depense.statut = "rejeté_admin"
        depense.commentaire_admin = commentaire

    depense.date_validation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db.commit()
    db.refresh(depense)

    log_action(db, current_user.id, "rejet dépense", "Depense", depense.id)

    return RedirectResponse(url=redirect_after_action(current_user), status_code=302)


# --- LISTE DES DÉPENSES ---
@router.get("/list")
def list_depenses(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(auth.require_role(["admin", "controleur", "agent"]))
):
    depenses = db.query(models.Depense).all()
    return templates.TemplateResponse("depenses_list.html", {
        "request": request,
        "depenses": depenses,
        "user": current_user
    })
