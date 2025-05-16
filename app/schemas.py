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
    role: Optional[Role] = Role.USER
    profilepic: Optional[str] = "/assets/profile.jpg"

from enum import Enum

class PropositionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

    
class WebSocketMessage(BaseModel):
    type: str
    data: dict        

class UtilisateurResponse(UtilisateurBase):
    id: int
    nom: str
    email: str
    role: str
    profilepic: Optional[str] = "/assets/profile.jpg"

    class Config:
        orm_mode = True

# Plante
class PlanteBase(BaseModel):
    name: str
    type: Optional[str] = None
    description: str
    image_url: Optional[str] = None

class PlanteCreate(BaseModel):
    name: str
    type: Optional[str] = None
    description: str
    image_url: Optional[str] = None

class PlanteResponse(BaseModel):
    id: int
    name: str
    type: Optional[str] = None
    description: str
    image_url: Optional[str] = None
    approuvee: bool
    proprietaire_id: Optional[int] = None
    created_by: str

    class Config:
        orm_mode = True
        from_attributes = True

# Proposition Plante
class PropositionPlanteBase(BaseModel):
    name: str
    type: Optional[str] = None
    description: str
    image_url: Optional[str] = None

class PropositionPlanteCreate(BaseModel):
    name: str
    type: Optional[str] = None
    description: str
    image_url: Optional[str] = None

class PropositionPlanteResponse(BaseModel):
    id: int
    name: str
    type: Optional[str] = None
    description: str
    image_url: Optional[str] = None
    statut: str
    utilisateur_id: Optional[int] = None

    class Config:
        orm_mode = True

# Conseil
class ConseilBase(BaseModel):
    titre: str
    description: str

class ConseilCreate(BaseModel):
    titre: str
    description: str
    plante_id: int

class ConseilResponse(BaseModel):
    id: int
    titre: str
    description: str
    plante_id: int
    auteur_id: int

    class Config:
        orm_mode = True

# Recommendation
class RecommendationBase(BaseModel):
    raison: str
    plante_id: int

class RecommendationCreate(BaseModel):
    raison: str
    plante_id: int

class RecommendationResponse(BaseModel):
    id: int
    raison: str
    plante_id: int
    utilisateur_id: int
    date: datetime

    class Config:
        orm_mode = True

# Token
class Token(BaseModel):
    access_token: str
    token_type: str
    user_role: str
    user_email: str

class TokenData(BaseModel):
    email: Optional[str] = None