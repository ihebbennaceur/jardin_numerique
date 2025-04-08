from fastapi import FastAPI, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal, engine, Base
import models, crud, schemas
from auth import create_access_token, decode_access_token

app = FastAPI()
Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token invalide")
    user = crud.get_user_by_id(db, int(user_id))
    if user is None:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
    return user

@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    return crud.create_user(db, user)

@app.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    auth_user = crud.authenticate_user(db, user.email, user.password)
    if not auth_user:
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    token = create_access_token(data={"sub": str(auth_user.id)})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/jardin", response_model=schemas.JardinOut)
def create_jardin(jardin: schemas.JardinCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.create_jardin(db, current_user.id, jardin)
