from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas, crud
from .database import engine, SessionLocal
from typing import List, Optional
import numpy as np
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
from fastapi import UploadFile, File
import shutil
import os

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Route pour l'inscription
@app.post("/inscription/")
def inscription(nom: str, email: str, mot_de_passe: str, db: Session = Depends(get_db)):
    utilisateur = models.Utilisateur.s_inscrire(db, nom, email, mot_de_passe)
    return {"message": "Inscription réussie", "utilisateur": {"id": utilisateur.id, "email": utilisateur.email}}

# Route pour la connexion
@app.post("/connexion/")
def connexion(email: str, mot_de_passe: str, db: Session = Depends(get_db)):
    utilisateur = models.Utilisateur.se_connecter(db, email, mot_de_passe)
    if not utilisateur:
        raise HTTPException(status_code=400, detail="Email ou mot de passe incorrect")
    return {"message": "Connexion réussie", "utilisateur": {"id": utilisateur.id, "email": utilisateur.email}}

# Route pour modifier le compte utilisateur
@app.put("/utilisateurs/{utilisateur_id}/")
def modifier_utilisateur(utilisateur_id: int, nom: Optional[str] = None, email: Optional[str] = None, db: Session = Depends(get_db)):
    utilisateur = db.query(models.Utilisateur).filter(models.Utilisateur.id == utilisateur_id).first()
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    utilisateur.gerer_compte(db, nom, email)
    return {"message": "Compte mis à jour", "utilisateur": {"id": utilisateur.id, "email": utilisateur.email}}

# # Routes pour Utilisateur
# @app.post("/utilisateurs/", response_model=schemas.UtilisateurResponse)
# def create_utilisateur(utilisateur: schemas.UtilisateurCreate, db: Session = Depends(get_db)):
#     return crud.create_utilisateur(db=db, utilisateur=utilisateur)

@app.get("/utilisateurs/{utilisateur_id}", response_model=schemas.UtilisateurResponse)
def read_utilisateur(utilisateur_id: int, db: Session = Depends(get_db)):
    db_utilisateur = crud.get_utilisateur(db, utilisateur_id=utilisateur_id)
    if db_utilisateur is None:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return db_utilisateur

@app.get("/utilisateurs/all", response_model=List[schemas.UtilisateurResponse])
def read_utilisateurs(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_utilisateurs(db, skip=skip, limit=limit)

# Routes pour Plante
@app.post("/plantes/", response_model=schemas.PlanteResponse)
def create_plante(plante: schemas.PlanteCreate, db: Session = Depends(get_db)):
    return crud.create_plante(db=db, plante=plante)

@app.get("/plantes/", response_model=List[schemas.PlanteResponse])
def read_plantes(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_plantes(db, skip=skip, limit=limit)

@app.delete("/plantes/{plante_id}/", response_model=dict)
def delete_plante(plante_id: int, db: Session = Depends(get_db)):
    plante = db.query(models.Plante).filter(models.Plante.id == plante_id).first()
    if not plante:
        raise HTTPException(status_code=404, detail="Plante non trouvée")
    db.delete(plante)
    db.commit()
    return {"message": f"Plante avec l'ID {plante_id} supprimée avec succès"}

# Routes pour Capteur
@app.post("/capteurs/", response_model=schemas.CapteurResponse)
def create_capteur(capteur: schemas.CapteurCreate, db: Session = Depends(get_db)):
    return crud.create_capteur(db=db, capteur=capteur)

@app.get("/capteurs/", response_model=List[schemas.CapteurResponse])
def read_capteurs(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_capteurs(db, skip=skip, limit=limit)

@app.get("/capteurs/{capteur_id}", response_model=schemas.CapteurResponse)
def read_capteur(capteur_id: int, db: Session = Depends(get_db)):
    db_capteur = crud.get_capteur(db, capteur_id=capteur_id)
    if db_capteur is None:
        raise HTTPException(status_code=404, detail="Capteur non trouvé")
    return db_capteur

# Routes pour Conseil
@app.post("/conseils/", response_model=schemas.ConseilResponse)
def create_conseil(conseil: schemas.ConseilCreate, db: Session = Depends(get_db)):
    return crud.create_conseil(db=db, conseil=conseil)

@app.get("/conseils/", response_model=List[schemas.ConseilResponse])
def read_conseils(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_conseils(db, skip=skip, limit=limit)

@app.get("/conseils/{conseil_id}", response_model=schemas.ConseilResponse)
def read_conseil(conseil_id: int, db: Session = Depends(get_db)):
    db_conseil = crud.get_conseil(db, conseil_id=conseil_id)
    if db_conseil is None:
        raise HTTPException(status_code=404, detail="Conseil non trouvé")
    return db_conseil

# Routes pour Produit
@app.post("/produits/", response_model=schemas.ProduitResponse)
def create_produit(produit: schemas.ProduitCreate, db: Session = Depends(get_db)):
    return crud.create_produit(db=db, produit=produit)

@app.get("/produits/", response_model=List[schemas.ProduitResponse])
def read_produits(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_produits(db, skip=skip, limit=limit)

@app.get("/produits/{produit_id}", response_model=schemas.ProduitResponse)
def read_produit(produit_id: int, db: Session = Depends(get_db)):
    db_produit = crud.get_produit(db, produit_id=produit_id)
    if db_produit is None:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return db_produit

model = ResNet50(weights='imagenet')

@app.post("/reconnaissance_plantes/image/")
async def reconnaitre_plante(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Sauvegarder temporairement l'image téléchargée
    temp_file_path = f"temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # Charger l'image et la redimensionner à 224x224 (taille attendue par ResNet50)
        img = image.load_img(temp_file_path, target_size=(224, 224))

        # Prétraiter l'image
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)

        # Prédire la classe
        preds = model.predict(x)
        decoded = decode_predictions(preds, top=5)[0]

        # Formater les résultats
        predictions = [{"label": label, "probability": float(prob)} for (_, label, prob) in decoded]

        # Retourner les prédictions
        return {"predictions": predictions}

    finally:
        # Supprimer le fichier temporaire
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)