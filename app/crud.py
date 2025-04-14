from sqlalchemy.orm import Session
from . import models, schemas

# Utilisateur
def create_utilisateur(db: Session, utilisateur: schemas.UtilisateurCreate):
    db_utilisateur = models.Utilisateur(
        nom=utilisateur.nom,
        email=utilisateur.email,
        mot_de_passe=utilisateur.mot_de_passe
    )
    db.add(db_utilisateur)
    db.commit()
    db.refresh(db_utilisateur)
    return db_utilisateur

def get_utilisateur(db: Session, utilisateur_id: int):
    return db.query(models.Utilisateur).filter(models.Utilisateur.id == utilisateur_id).first()

def get_utilisateurs(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Utilisateur).offset(skip).limit(limit).all()

# Plante
def create_plante(db: Session, plante: schemas.PlanteCreate):
    db_plante = models.Plante(
        nom=plante.nom,
        type=plante.type,
        photo=plante.photo,
        proprietaire_id=plante.proprietaire_id
    )
    db.add(db_plante)
    db.commit()
    db.refresh(db_plante)
    return db_plante

def get_plantes(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Plante).offset(skip).limit(limit).all()

# Capteur
def create_capteur(db: Session, capteur: schemas.CapteurCreate):
    db_capteur = models.Capteur(
        type=capteur.type,
        valeur=capteur.valeur,
        plante_id=capteur.plante_id
    )
    db.add(db_capteur)
    db.commit()
    db.refresh(db_capteur)
    return db_capteur

def get_capteurs(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Capteur).offset(skip).limit(limit).all()

def get_capteur(db: Session, capteur_id: int):
    return db.query(models.Capteur).filter(models.Capteur.id == capteur_id).first()

# Conseil
def create_conseil(db: Session, conseil: schemas.ConseilCreate):
    db_conseil = models.Conseil(
        texte=conseil.texte,
        type_plante=conseil.type_plante,
        plante_id=conseil.plante_id
    )
    db.add(db_conseil)
    db.commit()
    db.refresh(db_conseil)
    return db_conseil

def get_conseils(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Conseil).offset(skip).limit(limit).all()

def get_conseil(db: Session, conseil_id: int):
    return db.query(models.Conseil).filter(models.Conseil.id == conseil_id).first()

# Produit
def create_produit(db: Session, produit: schemas.ProduitCreate):
    db_produit = models.Produit(
        nom=produit.nom,
        description=produit.description,
        note=produit.note,
        utilisateur_id=produit.utilisateur_id
    )
    db.add(db_produit)
    db.commit()
    db.refresh(db_produit)
    return db_produit

def get_produits(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Produit).offset(skip).limit(limit).all()

def get_produit(db: Session, produit_id: int):
    return db.query(models.Produit).filter(models.Produit.id == produit_id).first()

# ReconnaissancePlante
def create_reconnaissance_plante(db: Session, reconnaissance: schemas.ReconnaissancePlanteCreate):
    db_reconnaissance = models.ReconnaissancePlante(
        message=reconnaissance.message,
        lu=reconnaissance.lu,
        utilisateur_id=reconnaissance.utilisateur_id
    )
    db.add(db_reconnaissance)
    db.commit()
    db.refresh(db_reconnaissance)
    return db_reconnaissance

def get_reconnaissance_plantes(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.ReconnaissancePlante).offset(skip).limit(limit).all()

def get_reconnaissance_plante(db: Session, reconnaissance_id: int):
    return db.query(models.ReconnaissancePlante).filter(models.ReconnaissancePlante.id == reconnaissance_id).first()
