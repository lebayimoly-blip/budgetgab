from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, auth
from app.utils.logs import log_action   # ← ajout important

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# --- PAGE FORMULAIRE : CRÉER UN BUDGET ---
@router.get("/create")
def create_budget_form(
    request: Request,
    current_user = Depends(auth.require_role(["admin"]))
):
    return templates.TemplateResponse("create_budget.html", {
        "request": request,
        "user": current_user
    })


# --- TRAITEMENT FORMULAIRE : CRÉATION DU BUDGET ---
@router.post("/create")
def create_budget(
    nom: str = Form(...),
    montant: float = Form(...),
    departement: str = Form(None),
    projet: str = Form(None),
    prevision: float = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(auth.require_role(["admin"]))
):
    budget = models.Budget(
        nom=nom,
        montant=montant,
        departement=departement,
        projet=projet,
        prevision=prevision
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)

    # Journaliser
    log_action(db, current_user.id, "création budget", "Budget", budget.id)

    return RedirectResponse(url="/dashboard", status_code=302)


# --- LISTE DES BUDGETS ---
# --- LISTE DES BUDGETS ---
@router.get("/list")
def list_budgets(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(auth.require_role(["admin"]))
):
    budgets = db.query(models.Budget).all()

    enriched_budgets = []
    for b in budgets:
        # ✅ Seules les dépenses validées (contrôleur ou admin) impactent le budget
        depenses = db.query(models.Depense).filter(
            models.Depense.budget_id == b.id,
            models.Depense.statut.in_(["validé_controleur", "approuvé_admin"])
        ).all()

        total_depenses = sum(d.montant for d in depenses)
        derniere_depense = depenses[-1].montant if depenses else 0
        restant = b.montant - total_depenses

        ecart = b.prevision - total_depenses if b.prevision is not None else None
        pourcentage = (total_depenses / b.montant * 100) if b.montant > 0 else 0

        if pourcentage < 70:
            alert_class = "green"
        elif pourcentage < 100:
            alert_class = "orange"
        else:
            alert_class = "red"

        enriched_budgets.append({
            "id": b.id,
            "nom": b.nom,
            "departement": b.departement,
            "projet": b.projet,
            "prevision": b.prevision,
            "montant": b.montant,
            "derniere_depense": derniere_depense,
            "restant": restant,
            "ecart": ecart,
            "pourcentage": round(pourcentage, 2),
            "alert_class": alert_class
        })

    return templates.TemplateResponse("list_budgets.html", {
        "request": request,
        "budgets": enriched_budgets,
        "user": current_user
    })
