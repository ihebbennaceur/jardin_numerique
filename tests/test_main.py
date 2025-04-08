import pytest
from fastapi.testclient import TestClient
from main import app
from database import Base, engine, SessionLocal
import models

client = TestClient(app)

def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_register_login_create_jardin():
    # 1. Inscription
    response = client.post("/register", json={"email": "test@example.com", "password": "secret"})
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

    # 2. Connexion
    response = client.post("/login", json={"email": "test@example.com", "password": "secret"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Création de jardin
    response = client.post("/jardin", json={"name": "Mon Jardin", "description": "Test description"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Mon Jardin"
