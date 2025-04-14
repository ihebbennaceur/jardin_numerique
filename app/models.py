from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Utilisateur(Base):
    __tablename__ = "utilisateurs"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    mot_de_passe = Column(String)
    plantes = relationship("Plante", back_populates="proprietaire")
    produits = relationship("Produit", back_populates="utilisateur")
    reconnaissances = relationship("ReconnaissancePlante", back_populates="utilisateur")

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @classmethod
    def s_inscrire(cls, db: Session, nom: str, email: str, mot_de_passe: str):
        hashed_password = cls.hash_password(mot_de_passe)
        utilisateur = cls(nom=nom, email=email, mot_de_passe=hashed_password)
        db.add(utilisateur)
        db.commit()
        db.refresh(utilisateur)
        return utilisateur

    @classmethod
    def se_connecter(cls, db: Session, email: str, mot_de_passe: str):
        utilisateur = db.query(cls).filter(cls.email == email).first()
        if utilisateur and cls.verify_password(mot_de_passe, utilisateur.mot_de_passe):
            return utilisateur
        return None

    def gerer_compte(self, db: Session, nom: Optional[str] = None, email: Optional[str] = None):
        if nom:
            self.nom = nom
        if email:
            self.email = email
        db.commit()
        db.refresh(self)
        return self
    


class Plante(Base):
    __tablename__ = "plantes"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, index=True)
    type = Column(String)
    photo = Column(String, nullable=True)
    proprietaire_id = Column(Integer, ForeignKey("utilisateurs.id"))
    proprietaire = relationship("Utilisateur", back_populates="plantes")
    capteurs = relationship("Capteur", back_populates="plante")
    conseils = relationship("Conseil", back_populates="plante")

    def ajouter_plante(self):
        # Logique pour ajouter une plante
        pass

    def supprimer_plante(self):
        # Logique pour supprimer une plante
        pass

class Capteur(Base):
    __tablename__ = "capteurs"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    valeur = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    plante_id = Column(Integer, ForeignKey("plantes.id"))
    plante = relationship("Plante", back_populates="capteurs")

    def envoyer_donnees(self):
        # Logique pour envoyer des données
        pass

class Conseil(Base):
    __tablename__ = "conseils"
    id = Column(Integer, primary_key=True, index=True)
    texte = Column(String)
    type_plante = Column(String)
    plante_id = Column(Integer, ForeignKey("plantes.id"))
    plante = relationship("Plante", back_populates="conseils")

    def generer_conseil(self):
        # Logique pour générer un conseil
        pass

class Produit(Base):
    __tablename__ = "produits"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, index=True)
    description = Column(String)
    note = Column(Float)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"))
    utilisateur = relationship("Utilisateur", back_populates="produits")

    def comparer(self):
        # Logique pour comparer des produits
        pass

class ReconnaissancePlante(Base):
    __tablename__ = "reconnaissance_plantes"
    id = Column(Integer, primary_key=True, index=True)
    message = Column(String)
    lu = Column(Boolean, default=False)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"))
    utilisateur = relationship("Utilisateur", back_populates="reconnaissances")

    def envoyer(self):
        # Logique pour envoyer une reconnaissance
        pass