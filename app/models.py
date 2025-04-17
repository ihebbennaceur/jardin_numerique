from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database import Base
from enum import Enum as PyEnum

class Role(str, PyEnum):
    USER = "user"
    ADMIN = "admin"

class Utilisateur(Base):
    __tablename__ = "utilisateurs"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    mot_de_passe = Column(String)
    role = Column(Enum(Role), default=Role.USER)  # Par défaut, le rôle est "user"
    plantes = relationship("Plante", back_populates="proprietaire")  # Relation avec Plante
    propositions = relationship("PropositionPlante", back_populates="utilisateur")
    conseils = relationship("Conseil", back_populates="auteur")


class Plante(Base):
    __tablename__ = "plantes"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, index=True)
    type = Column(String)
    description = Column(String)
    photo = Column(String, nullable=True)
    approuvee = Column(Boolean, default=False)
    proprietaire_id = Column(Integer, ForeignKey("utilisateurs.id"))
    proprietaire = relationship("Utilisateur", back_populates="plantes")  # Relation avec Utilisateur
    conseils = relationship("Conseil", back_populates="plante")

class PropositionPlante(Base):
    __tablename__ = "propositions_plantes"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String)
    type = Column(String)
    description = Column(String)
    photo = Column(String, nullable=True)
    statut = Column(String, default="en_attente")  # en_attente, approuvee, rejetee
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"))
    utilisateur = relationship("Utilisateur", back_populates="propositions")

class Conseil(Base):
    __tablename__ = "conseils"
    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String)
    description = Column(String)
    plante_id = Column(Integer, ForeignKey("plantes.id"))
    plante = relationship("Plante", back_populates="conseils")
    auteur_id = Column(Integer, ForeignKey("utilisateurs.id"))
    auteur = relationship("Utilisateur", back_populates="conseils")

class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(Integer, primary_key=True, index=True)
    plante_id = Column(Integer, ForeignKey("plantes.id"))
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"))
    raison = Column(String)
    date = Column(String)