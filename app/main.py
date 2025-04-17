from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas, crud
from database import SessionLocal, engine
from auth import create_access_token, decode_access_token, verify_password, get_password_hash
from datetime import timedelta
import os
from pydantic import BaseModel

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ------------------ AUTHENTIFICATION ------------------
from fastapi import Request  # Ajoutez cette importation
@app.post("/admin/creer_admin", response_model=schemas.UtilisateurResponse)
def creer_admin(utilisateur: schemas.UtilisateurCreate, db: Session = Depends(get_db)):
    # Vérifiez si un admin existe déjà
    admin_existant = db.query(models.Utilisateur).filter(models.Utilisateur.role == "admin").first()
    if admin_existant:
        raise HTTPException(status_code=400, detail="Un admin existe déjà.")
    
    # Créez l'utilisateur avec le rôle admin
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
        data={"sub": user.email},
        expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}
@app.post("/inscription", response_model=schemas.UtilisateurResponse)
def inscription(utilisateur: schemas.UtilisateurCreate, db: Session = Depends(get_db)):
    db_user = crud.get_utilisateur_by_email(db, email=utilisateur.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email déjà enregistré")
    return crud.create_utilisateur(db=db, utilisateur=utilisateur)

# ------------------ FONCTIONNALITÉS UTILISATEUR ------------------
@app.get("/utilisateurs/me", response_model=schemas.UtilisateurResponse)
def lire_utilisateur_courant(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token invalide")
    user = crud.get_utilisateur_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user

@app.put("/utilisateurs/me")
def modifier_utilisateur(
    nom: Optional[str] = None,
    email: Optional[str] = None,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    email_token = decode_access_token(token)
    if not email_token:
        raise HTTPException(status_code=401, detail="Token invalide")
    user = crud.get_utilisateur_by_email(db, email_token)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    if nom:
        user.nom = nom
    if email:
        user.email = email
    
    db.commit()
    db.refresh(user)
    return user

@app.get("/plantes", response_model=List[schemas.PlanteResponse])
def lire_plantes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_plantes(db, skip=skip, limit=limit)

@app.get("/plantes/{plante_id}", response_model=schemas.PlanteResponse)
def lire_plante(plante_id: int, db: Session = Depends(get_db)):
    plante = crud.get_plante(db, plante_id)
    if not plante:
        raise HTTPException(status_code=404, detail="Plante non trouvée")
    return plante

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
    return crud.create_plante(db, plante, user.id)

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
    return crud.create_proposition_plante(db, proposition, user.id)

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
    return plante

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