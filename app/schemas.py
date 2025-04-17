from pydantic import BaseModel
from typing import Optional, List
from enum import Enum
from datetime import datetime

class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"

# Utilisateur
class UtilisateurBase(BaseModel):
    nom: str
    email: str

class LoginRequest(BaseModel):
    email: str
    password: str
    
class UtilisateurCreate(BaseModel):
    nom: str
    email: str
    mot_de_passe: str
    role: Optional[Role] = Role.USER  # Par défaut, le rôle est "user"

class UtilisateurResponse(UtilisateurBase):
    id: int
    role: Role
    class Config:
        orm_mode = True

# Plante
class PlanteBase(BaseModel):
    nom: str
    type: str
    description: str

class PlanteCreate(PlanteBase):
    pass

class PlanteResponse(PlanteBase):
    id: int
    approuvee: bool
    proprietaire_id: int
    class Config:
        orm_mode = True

# Proposition Plante
class PropositionPlanteBase(BaseModel):
    nom: str
    type: str
    description: str

class PropositionPlanteCreate(PropositionPlanteBase):
    pass

class PropositionPlanteResponse(PropositionPlanteBase):
    id: int
    statut: str
    utilisateur_id: int
    class Config:
        orm_mode = True

# Conseil
class ConseilBase(BaseModel):
    titre: str
    description: str

class ConseilCreate(ConseilBase):
    plante_id: int

class ConseilResponse(ConseilBase):
    id: int
    plante_id: int
    auteur_id: int
    class Config:
        orm_mode = True

# Recommendation
class RecommendationBase(BaseModel):
    raison: str
    plante_id: int

class RecommendationCreate(RecommendationBase):
    pass

class RecommendationResponse(RecommendationBase):
    id: int
    utilisateur_id: int
    date: datetime
    class Config:
        orm_mode = True

# Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None