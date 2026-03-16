from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes import rapports
from fastapi.staticfiles import StaticFiles


from fastapi.responses import HTMLResponse

from app.routes import budgets, engagements, depenses, factures, dashboard, users
from app.database import Base, engine

# Création des tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gestion Budgétaire")

# Statiques et templates
app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount("/uploads", StaticFiles(directory="app/uploads"), name="uploads")

templates = Jinja2Templates(directory="app/templates")

# --- PAGE D’ACCUEIL = LOGIN ---
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Routes
app.include_router(users.router, prefix="/users", tags=["Utilisateurs"])
app.include_router(budgets.router, prefix="/budgets", tags=["Budgets"])
app.include_router(engagements.router, prefix="/engagements", tags=["Engagements"])
app.include_router(depenses.router, prefix="/depenses", tags=["Dépenses"])
app.include_router(factures.router, prefix="/factures", tags=["Factures"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(rapports.router, prefix="")
