from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def list_engagements():
    return {"message": "Liste des engagements (à implémenter)"}
