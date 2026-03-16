from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models

def test_relations():
    db: Session = SessionLocal()

    # 1. Créer un utilisateur
    user = models.User(username="agent_test2", hashed_password="xxx", role="agent")
    db.add(user)
    db.commit()
    db.refresh(user)

    # 2. Créer un budget
    budget = models.Budget(nom="Budget Santé", montant=100000, departement="Santé", projet="Projet Vaccination")
    db.add(budget)
    db.commit()
    db.refresh(budget)

    # 3. Créer une dépense liée à l’utilisateur et au budget
    depense = models.Depense(description="Achat matériel médical", montant=5000, budget_id=budget.id, user_id=user.id)
    db.add(depense)
    db.commit()
    db.refresh(depense)

    # 4. Créer une facture liée à la dépense
    facture = models.Facture(fichier="factures/test.pdf", type_fichier="pdf", depense_id=depense.id)
    db.add(facture)
    db.commit()
    db.refresh(facture)

    # 5. Créer une action de log
    log = models.LogAction(user_id=user.id, action="création dépense", cible_type="Depense", cible_id=depense.id)
    db.add(log)
    db.commit()
    db.refresh(log)

    # --- Vérifications ---
    print("Utilisateur:", user.username, "→ Dépenses:", [d.description for d in user.depenses])
    print("Budget:", budget.nom, "→ Dépenses:", [d.description for d in budget.depenses])
    print("Dépense:", depense.description, "→ User:", depense.user.username, "→ Facture:", depense.facture.fichier)
    print("Log:", log.action, "→ User:", log.user.username)

    db.close()

if __name__ == "__main__":
    test_relations()
