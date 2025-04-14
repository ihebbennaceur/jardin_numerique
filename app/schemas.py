from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Utilisateur
class UtilisateurBase(BaseModel):
    nom: str
    email: str

class UtilisateurCreate(UtilisateurBase):
    mot_de_passe: str

class UtilisateurResponse(UtilisateurBase):
    id: int
    class Config:
        orm_mode = True

# Plante
class PlanteBase(BaseModel):
    nom: str
    type: str
    photo: Optional[str] = None

class PlanteCreate(PlanteBase):
    proprietaire_id: int

class PlanteResponse(PlanteBase):
    id: int
    class Config:
        orm_mode = True

# Capteur
class CapteurBase(BaseModel):
    type: str
    valeur: float

class CapteurCreate(CapteurBase):
    plante_id: int

class CapteurResponse(CapteurBase):
    id: int
    timestamp: datetime
    class Config:
        orm_mode = True

# Conseil
class ConseilBase(BaseModel):
    texte: str
    type_plante: str

class ConseilCreate(ConseilBase):
    plante_id: int

class ConseilResponse(ConseilBase):
    id: int
    class Config:
        orm_mode = True

# Produit
class ProduitBase(BaseModel):
    nom: str
    description: str
    note: float

class ProduitCreate(ProduitBase):
    utilisateur_id: int

class ProduitResponse(ProduitBase):
    id: int
    class Config:
        orm_mode = True

# ReconnaissancePlante
class ReconnaissancePlanteBase(BaseModel):
    message: str
    lu: bool = False

class ReconnaissancePlanteCreate(ReconnaissancePlanteBase):
    utilisateur_id: int

class ReconnaissancePlanteResponse(ReconnaissancePlanteBase):
    id: int
    class Config:
        orm_mode = True