from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, auth

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload/{depense_id}")
async def upload_facture(
    depense_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(auth.get_current_user_from_cookie)
):
    filename = f"static/{file.filename}"
    with open(filename, "wb") as f:
        f.write(await file.read())
    facture = models.Facture(fichier=filename, depense_id=depense_id)
    db.add(facture)
    db.commit()
    db.refresh(facture)
    return {"message": f"Facture ajoutée par {current_user.username}", "facture": facture.fichier}
