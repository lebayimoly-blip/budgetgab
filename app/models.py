from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="agent")  # agent, controleur, admin

    # Relations inverses
    depenses = relationship("Depense", back_populates="user")
    logs = relationship("LogAction", back_populates="user")


class Budget(Base):
    __tablename__ = "budgets"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, unique=True, index=True)
    montant = Column(Float)

    departement = Column(String, nullable=True)   # ex: "Santé", "Éducation"
    projet = Column(String, nullable=True)        # ex: "Projet X"
    prevision = Column(Float, nullable=True)

    # Relation inverse
    depenses = relationship("Depense", back_populates="budget")


from datetime import datetime

class Depense(Base):
    __tablename__ = "depenses"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String)
    montant = Column(Float)

    budget_id = Column(Integer, ForeignKey("budgets.id"))
    budget = relationship("Budget", back_populates="depenses")

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="depenses")

    statut = Column(String, default="en_attente")
    commentaire_controleur = Column(String, nullable=True)
    commentaire_admin = Column(String, nullable=True)   # ← AJOUT ICI
    date_validation = Column(String, nullable=True)
    date_creation = Column(DateTime, default=datetime.utcnow)

    facture = relationship("Facture", back_populates="depense", uselist=False)



class Facture(Base):
    __tablename__ = "factures"
    id = Column(Integer, primary_key=True, index=True)
    fichier = Column(String)  # chemin du fichier stocké
    type_fichier = Column(String, nullable=True)  # ex: "pdf", "jpg", "png"

    depense_id = Column(Integer, ForeignKey("depenses.id"))
    depense = relationship("Depense", back_populates="facture")


class LogAction(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String)        # ex: "création dépense", "validation", "rejet"
    cible_type = Column(String)    # ex: "Budget", "Depense"
    cible_id = Column(Integer)     # ID de l’objet concerné
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="logs")
