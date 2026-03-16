from fastapi import APIRouter, Depends, Request
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

@router.get("/")
def dashboard_root(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user_from_cookie)
):
    role = current_user.role

    if role == "admin":
        return templates.TemplateResponse("dashboard_admin.html", {
            "request": request,
            "user": current_user
        })

    if role == "controleur":
        return templates.TemplateResponse("dashboard_controleur.html", {
            "request": request,
            "user": current_user
        })

    # Agent par défaut
    return templates.TemplateResponse("dashboard_agent.html", {
        "request": request,
        "user": current_user
    })

@router.get("/logs")
def list_logs(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(auth.require_role(["admin"]))
):
    logs = db.query(models.LogAction).order_by(models.LogAction.timestamp.desc()).all()
    return templates.TemplateResponse("logs_list.html", {
        "request": request,
        "logs": logs,
        "user": current_user
    })

# --- DASHBOARD CONTROLEUR ---
@router.get("/controleur")
def dashboard_controleur(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(auth.require_role(["controleur"]))
):
    # Dépenses en attente
    depenses = db.query(models.Depense).filter(
        models.Depense.statut == "en_attente"
    ).all()

    # Statistiques globales
    total = db.query(models.Depense).count()
    en_attente = db.query(models.Depense).filter(models.Depense.statut == "en_attente").count()
    validees = db.query(models.Depense).filter(
        models.Depense.statut.in_(["validé_controleur", "approuvé_admin"])
    ).count()
    rejetees = db.query(models.Depense).filter(
        models.Depense.statut.in_(["rejeté_controleur", "rejeté_admin"])
    ).count()

    # Historique des actions du contrôleur (les 5 dernières)
    logs = db.query(models.LogAction).filter(
        models.LogAction.user_id == current_user.id
    ).order_by(models.LogAction.timestamp.desc()).limit(5).all()


    # Budgets actifs
    budgets = db.query(models.Budget).all()
    budgets_data = []
    for b in budgets:
        montant_consomme = sum([d.montant for d in b.depenses if d.statut in ["validé_controleur", "approuvé_admin"]])
        solde = b.montant - montant_consomme
        budgets_data.append({
            "nom": b.nom,
            "montant_initial": b.montant,
            "montant_consomme": montant_consomme,
            "solde": solde
        })

     
    return templates.TemplateResponse("dashboard_controleur.html", {
        "request": request,
        "depenses": depenses,
        "total": total,
        "en_attente": en_attente,
        "validees": validees,
        "rejetees": rejetees,
        "logs": logs,
        "budgets": budgets_data,
        "user": current_user
    })

# --- DASHBOARD ADMIN ---
@router.get("/admin")
def dashboard_admin(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(auth.require_role(["admin"]))
):
    total = db.query(models.Depense).count()

    en_attente = db.query(models.Depense).filter(
        models.Depense.statut == "en_attente"
    ).count()

    # ✅ Seules les dépenses validées impactent
    validees = db.query(models.Depense).filter(
        models.Depense.statut.in_(["validé_controleur", "approuvé_admin"])
    ).count()

    rejetees = db.query(models.Depense).filter(
        models.Depense.statut.in_(["rejeté_controleur", "rejeté_admin"])
    ).count()

    return templates.TemplateResponse("dashboard_admin.html", {
        "request": request,
        "total": total,
        "en_attente": en_attente,
        "validees": validees,
        "rejetees": rejetees,
        "user": current_user
    })


# --- DASHBOARD AGENT ---
@router.get("/agent")
def dashboard_agent(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(auth.require_role(["agent", "controleur", "admin"]))
):
    depenses = db.query(models.Depense).filter(models.Depense.user_id == current_user.id).all()

    return templates.TemplateResponse("dashboard_agent.html", {
        "request": request,
        "depenses": depenses,
        "user": current_user
    })

@router.get("/depenses")
def dashboard_depenses(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(auth.require_role(["admin"]))
):
    depenses = db.query(models.Depense).all()
    return templates.TemplateResponse("depenses_list.html", {
        "request": request,
        "depenses": depenses,
        "user": current_user
    })

@router.get("/admin/controle")
def dashboard_admin_controle(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(auth.require_role(["admin"]))
):
    # Onglet 1 : Dépenses en attente (admin peut valider/rejeter)
    en_attente = db.query(models.Depense).filter(
        models.Depense.statut == "en_attente"
    ).all()

    # Onglet 2 : Dépenses validées (global)
    validees = db.query(models.Depense).filter(
        models.Depense.statut.in_(["validé_controleur", "approuvé_admin"])
    ).all()

    # Onglet 3 : Dépenses rejetées (global)
    rejetees = db.query(models.Depense).filter(
        models.Depense.statut.in_(["rejeté_controleur", "rejeté_admin"])
    ).all()

    return templates.TemplateResponse("dashboard_admin_controle.html", {
        "request": request,
        "en_attente": en_attente,
        "validees": validees,
        "rejetees": rejetees,
        "user": current_user
    })
