from pydantic import BaseModel

class BudgetBase(BaseModel):
    nom: str
    montant: float

class DepenseBase(BaseModel):
    description: str
    montant: float
    budget_id: int

class FactureBase(BaseModel):
    fichier: str
    depense_id: int
