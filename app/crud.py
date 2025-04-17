from sqlalchemy.orm import Session
import models, schemas
from auth import get_password_hash
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

# Utilisateur
from sqlalchemy.orm import Session
import models, schemas
from auth import get_password_hash

def create_utilisateur(db: Session, utilisateur: schemas.UtilisateurCreate):
    hashed_password = get_password_hash(utilisateur.mot_de_passe)
    db_utilisateur = models.Utilisateur(
        nom=utilisateur.nom,
        email=utilisateur.email,
        mot_de_passe=hashed_password,
        role=utilisateur.role  # Utilise le rôle fourni ou "user" par défaut
    )
    db.add(db_utilisateur)
    db.commit()
    db.refresh(db_utilisateur)
    return db_utilisateur

def get_utilisateur(db: Session, utilisateur_id: int):
    return db.query(models.Utilisateur).filter(models.Utilisateur.id == utilisateur_id).first()

def get_utilisateur_by_email(db: Session, email: str):
    return db.query(models.Utilisateur).filter(models.Utilisateur.email == email).first()

def get_utilisateurs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Utilisateur).offset(skip).limit(limit).all()

# Plante
def create_plante(db: Session, plante: schemas.PlanteCreate, user_id: int):
    db_plante = models.Plante(
        **plante.dict(),
        proprietaire_id=user_id,
        approuvee=True if db.query(models.Utilisateur).filter(
            models.Utilisateur.id == user_id,
            models.Utilisateur.role == "admin"
        ).first() else False
    )
    db.add(db_plante)
    db.commit()
    db.refresh(db_plante)
    return db_plante

def get_plantes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Plante).filter(models.Plante.approuvee == True).offset(skip).limit(limit).all()

def get_plante(db: Session, plante_id: int):
    return db.query(models.Plante).filter(models.Plante.id == plante_id).first()

def delete_plante(db: Session, plante_id: int):
    plante = db.query(models.Plante).filter(models.Plante.id == plante_id).first()
    if plante:
        db.delete(plante)
        db.commit()
        return True
    return False

# Proposition Plante
def create_proposition_plante(db: Session, proposition: schemas.PropositionPlanteCreate, user_id: int):
    db_proposition = models.PropositionPlante(
        **proposition.dict(),
        utilisateur_id=user_id
    )
    db.add(db_proposition)
    db.commit()
    db.refresh(db_proposition)
    return db_proposition

def get_propositions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.PropositionPlante).offset(skip).limit(limit).all()

def valider_proposition(db: Session, proposition_id: int):
    proposition = db.query(models.PropositionPlante).filter(models.PropositionPlante.id == proposition_id).first()
    if not proposition:
        return None
    
    proposition.statut = "approuvee"
    
    plante = models.Plante(
        nom=proposition.nom,
        type=proposition.type,
        description=proposition.description,
        photo=proposition.photo,
        approuvee=True,
        proprietaire_id=proposition.utilisateur_id
    )
    db.add(plante)
    db.commit()
    db.refresh(plante)
    return plante

# Conseil
def create_conseil(db: Session, conseil: schemas.ConseilCreate, user_id: int):
    db_conseil = models.Conseil(
        **conseil.dict(),
        auteur_id=user_id
    )
    db.add(db_conseil)
    db.commit()
    db.refresh(db_conseil)
    return db_conseil

def get_conseils(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Conseil).offset(skip).limit(limit).all()

def get_conseils_plante(db: Session, plante_id: int):
    return db.query(models.Conseil).filter(models.Conseil.plante_id == plante_id).all()

# Recommendation
def create_recommendation(db: Session, recommendation: schemas.RecommendationCreate, user_id: int):
    db_recommendation = models.Recommendation(
        **recommendation.dict(),
        utilisateur_id=user_id,
        date=str(datetime.now())
    )
    db.add(db_recommendation)
    db.commit()
    db.refresh(db_recommendation)
    return db_recommendation

def get_recommendations_utilisateur(db: Session, user_id: int):
    return db.query(models.Recommendation).filter(models.Recommendation.utilisateur_id == user_id).all()