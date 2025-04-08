from sqlalchemy.orm import Session
from app.models import User, Jardin
from app.schemas import UserCreate, JardinCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_user(db: Session, user: UserCreate):
    hashed = get_password_hash(user.password)
    db_user = User(username=user.username,email=user.email, hashed_password=hashed)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_jardin(db: Session, user_id: int, jardin: JardinCreate):
    db_jardin = Jardin(**jardin.dict(), owner_id=user_id)
    db.add(db_jardin)
    db.commit()
    db.refresh(db_jardin)
    return db_jardin

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()
