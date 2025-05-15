from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas, crud
from database import SessionLocal, engine
from auth import create_access_token, decode_access_token, verify_password, get_password_hash
from datetime import timedelta
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from models import Base, Utilisateur
from auth import get_current_user 
from passlib.context import CryptContext
from fastapi.staticfiles import StaticFiles
import os
import shutil
import uuid

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/uploads", StaticFiles(directory="Uploads"), name="uploads")

origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory exists
UPLOAD_DIR = "Uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ------------------ IMAGE UPLOAD ------------------
@app.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme)
):
    # Verify user authentication
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token invalide")
    
    # Validate file type
    allowed_extensions = {".png", ".jpg", ".jpeg"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Only PNG, JPG, or JPEG files are allowed")
    
    # Validate file size (e.g., max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB in bytes
    file_size = 0
    for chunk in file.file:
        file_size += len(chunk)
        if file_size > max_size:
            raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")
    file.file.seek(0)  # Reset file pointer
    
    # Generate unique filename
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, file_name)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
    
    # Return the relative path
    return {"image_url": f"/Uploads/{file_name}"}

# ------------------ AUTHENTIFICATION ------------------
@app.post("/admin/creer_admin", response_model=schemas.UtilisateurResponse)
def creer_admin(utilisateur: schemas.UtilisateurCreate, db: Session = Depends(get_db)):
    utilisateur_existant = db.query(models.Utilisateur).filter(models.Utilisateur.email == utilisateur.email).first()
    if utilisateur_existant:
        raise HTTPException(status_code=400, detail="Un utilisateur avec cet email existe déjà.")
    
    admin_existant = db.query(models.Utilisateur).filter(models.Utilisateur.role == "admin").first()
    if admin_existant:
        raise HTTPException(status_code=400, detail="Un admin existe déjà.")
    
    if not utilisateur.profilepic:
        utilisateur.profilepic = "assets/profile.jpg"
    
    utilisateur.role = "admin"
    return crud.create_utilisateur(db=db, utilisateur=utilisateur)

@app.post("/login", response_model=schemas.Token)
async def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    email = data.email
    password = data.password

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email et mot de passe sont requis pour se connecter"
        )
    
    user = crud.get_utilisateur_by_email(db, email)
    if not user or not verify_password(password, user.mot_de_passe):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=timedelta(minutes=30)
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_role": user.role,
        "user_email": user.email
    }

@app.post("/inscription", response_model=schemas.UtilisateurResponse)
def inscription(utilisateur: schemas.UtilisateurCreate, db: Session = Depends(get_db)):
    db_user = crud.get_utilisateur_by_email(db, email=utilisateur.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email déjà enregistré")
    return crud.create_utilisateur(db=db, utilisateur=utilisateur)

# ------------------ FONCTIONNALITÉS UTILISATEUR ------------------
@app.get("/utilisateurs/me", response_model=schemas.UtilisateurResponse)
def lire_utilisateur_courant(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    user = db.query(Utilisateur).filter(Utilisateur.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
class UtilisateurUpdate(BaseModel):
    nom: str
    email: str
    mot_de_passe: Optional[str] = None
    photo: Optional[str] = None

@app.put("/utilisateurs/me")
async def modifier_utilisateur(
    utilisateur: UtilisateurUpdate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    user = db.query(Utilisateur).filter(Utilisateur.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    user.nom = utilisateur.nom
    user.email = utilisateur.email

    if utilisateur.mot_de_passe:
        user.mot_de_passe = pwd_context.hash(utilisateur.mot_de_passe)

    if utilisateur.photo:
        user.profilepic = utilisateur.photo

    db.commit()
    db.refresh(user)
    return {"message": "Profil mis à jour avec succès"}

@app.get("/plantes", response_model=List[schemas.PlanteResponse])
def lire_plantes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    plantes = crud.get_plantes(db, skip=skip, limit=limit)
    return [
        schemas.PlanteResponse(
            id=plante.id,
            name=plante.name,
            type=plante.type,
            description=plante.description,
            image_url=plante.image_url,
            approuvee=plante.approuvee,
            proprietaire_id=plante.proprietaire_id,
            created_by=plante.proprietaire.nom
        ) for plante in plantes
    ]

@app.get("/plantes/{plante_id}", response_model=schemas.PlanteResponse)
def lire_plante(plante_id: int, db: Session = Depends(get_db)):
    plante = crud.get_plante(db, plante_id)
    if not plante:
        raise HTTPException(status_code=404, detail="Plante non trouvée")
    return schemas.PlanteResponse(
        id=plante.id,
        name=plante.name,
        type=plante.type,
        description=plante.description,
        image_url=plante.image_url,
        approuvee=plante.approuvee,
        proprietaire_id=plante.proprietaire_id,
        created_by=plante.proprietaire.nom
    )

@app.post("/plantes", response_model=schemas.PlanteResponse)
def ajouter_plante(
    plante: schemas.PlanteCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token invalide")
    user = crud.get_utilisateur_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    db_plante = crud.create_plante(db, plante, user.id)
    return schemas.PlanteResponse(
        id=db_plante.id,
        name=db_plante.name,
        type=db_plante.type,
        description=db_plante.description,
        image_url=db_plante.image_url,
        approuvee=db_plante.approuvee,
        proprietaire_id=db_plante.proprietaire_id,
        created_by=user.nom
    )

@app.post("/propositions", response_model=schemas.PropositionPlanteResponse)
def proposer_plante(
    proposition: schemas.PropositionPlanteCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token invalide")
    user = crud.get_utilisateur_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    db_proposition = crud.create_proposition_plante(db, proposition, user.id)
    return schemas.PropositionPlanteResponse(
        id=db_proposition.id,
        name=db_proposition.name,
        type=db_proposition.type,
        description=db_proposition.description,
        image_url=db_proposition.image_url,
        statut=db_proposition.statut,
        utilisateur_id=db_proposition.utilisateur_id
    )

@app.get("/propositions/me", response_model=List[schemas.PropositionPlanteResponse])
def lire_mes_propositions(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token invalide")
    user = crud.get_utilisateur_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    propositions = crud.get_user_propositions(db, user_id=user.id)
    return [
        schemas.PropositionPlanteResponse(
            id=prop.id,
            name=prop.name,
            type=prop.type,
            description=prop.description,
            image_url=prop.image_url,
            statut=prop.statut,
            utilisateur_id=prop.utilisateur_id
        ) for prop in propositions
    ]

@app.get("/plantes/{plante_id}/conseils", response_model=List[schemas.ConseilResponse])
def lire_conseils_plante(plante_id: int, db: Session = Depends(get_db)):
    return crud.get_conseils_plante(db, plante_id)

@app.post("/conseils", response_model=schemas.ConseilResponse)
def ajouter_conseil(
    conseil: schemas.ConseilCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token invalide")
    user = crud.get_utilisateur_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return crud.create_conseil(db, conseil, user.id)

@app.get("/recommendations", response_model=List[schemas.RecommendationResponse])
def lire_recommandations(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token invalide")
    user = crud.get_utilisateur_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return crud.get_recommendations_utilisateur(db, user.id)

# ------------------ FONCTIONNALITÉS ADMIN ------------------
@app.get("/admin/propositions", response_model=List[schemas.PropositionPlanteResponse])
def lire_propositions_admin(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token invalide")
    user = crud.get_utilisateur_by_email(db, email)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission refusée")
    return crud.get_propositions(db, skip=skip, limit=limit)


@app.post("/admin/propositions/{proposition_id}/rejeter")
def rejeter_proposition(
    proposition_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token invalide")
    user = crud.get_utilisateur_by_email(db, email)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission refusée")
    
    proposition = crud.reject_proposition(db, proposition_id)
    if not proposition:
        raise HTTPException(status_code=404, detail="Proposition non trouvée")
    return {"message": "Proposition rejetée avec succès"}


@app.post("/admin/propositions/{proposition_id}/valider", response_model=schemas.PlanteResponse)
def valider_proposition(
    proposition_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token invalide")
    user = crud.get_utilisateur_by_email(db, email)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission refusée")
    
    plante = crud.valider_proposition(db, proposition_id)
    if not plante:
        raise HTTPException(status_code=404, detail="Proposition non trouvée")
    return schemas.PlanteResponse(
        id=plante.id,
        name=plante.name,
        type=plante.type,
        description=plante.description,
        image_url=plante.image_url,
        approuvee=plante.approuvee,
        proprietaire_id=plante.proprietaire_id,
        created_by=plante.proprietaire.nom
    )

@app.delete("/admin/plantes/{plante_id}")
def supprimer_plante_admin(
    plante_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token invalide")
    user = crud.get_utilisateur_by_email(db, email)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission refusée")
    
    if not crud.delete_plante(db, plante_id):
        raise HTTPException(status_code=404, detail="Plante non trouvée")
    return {"message": "Plante supprimée avec succès"}

@app.get("/admin/utilisateurs", response_model=List[schemas.UtilisateurResponse])
def lire_utilisateurs_admin(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token invalide")
    user = crud.get_utilisateur_by_email(db, email)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Permission refusée")
    return crud.get_utilisateurs(db, skip=skip, limit=limit)

