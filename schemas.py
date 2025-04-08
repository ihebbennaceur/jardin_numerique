from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    class Config:
        orm_mode = True

class JardinCreate(BaseModel):
    name: str
    description: Optional[str] = None

class JardinOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    class Config:
        orm_mode = True
