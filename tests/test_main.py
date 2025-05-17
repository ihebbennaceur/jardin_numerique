import pytest
import os
import shutil
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app, get_db
from app.database import Base
from app.models import Utilisateur, Plante, PropositionPlante, Notification
from app.auth import create_access_token, get_password_hash, verify_password
from datetime import timedelta
import uuid

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# Fixtures
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test.db"):
        try:
            os.remove("test.db")
        except PermissionError:
            pass
    if os.path.exists("uploads"):
        shutil.rmtree("uploads")

@pytest.fixture
def test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_unique_user(email_prefix="user"):
    return {
        "nom": "Test User",
        "email": f"{email_prefix}_{uuid.uuid4().hex[:6]}@example.com",
        "mot_de_passe": "testpassword",
        "role": "user",
        "profilepic": "assets/profile.jpg"
    }

def create_and_commit_user(db, user_data):
    hashed = get_password_hash(user_data["mot_de_passe"])
    user = Utilisateur(
        nom=user_data["nom"],
        email=user_data["email"],
        mot_de_passe=hashed,
        role=user_data["role"],
        profilepic=user_data["profilepic"]
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_user(test_db):
    user_data = create_unique_user("user")
    return create_and_commit_user(test_db, user_data)

@pytest.fixture
def test_admin(test_db):
    admin_data = create_unique_user("admin")
    admin_data["role"] = "admin"
    return create_and_commit_user(test_db, admin_data)

@pytest.fixture
def user_token(test_user):
    token = create_access_token(
        data={"sub": test_user.email, "role": test_user.role},
        expires_delta=timedelta(minutes=30)
    )
    return token

@pytest.fixture
def admin_token(test_admin):
    token = create_access_token(
        data={"sub": test_admin.email, "role": test_admin.role},
        expires_delta=timedelta(minutes=30)
    )
    return token

# Unit tests
def test_create_access_token():
    data = {"sub": "test@example.com", "role": "user"}
    token = create_access_token(data, expires_delta=timedelta(minutes=30))
    assert isinstance(token, str) and len(token) > 0

def test_password_hashing():
    password = "testpassword"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed)

# Integration tests
def test_create_admin():
    email = f"admin_{uuid.uuid4().hex[:6]}@test.com"
    response = client.post("/admin/creer_admin", json={
        "nom": "Admin Test",
        "email": email,
        "mot_de_passe": "adminpass123",
        "profilepic": "assets/profile.jpg"
    })
    assert response.status_code == 200
    assert response.json()["email"] == email
    assert response.json()["role"] == "admin"

def test_login_success(test_user):
    response = client.post("/login", json={
        "email": test_user.email,
        "password": "testpassword"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_credentials(test_user):
    response = client.post("/login", json={
        "email": test_user.email,
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_upload_image(user_token):
    with open("test_image.jpg", "wb") as f:
        f.write(b"fake image content")
    with open("test_image.jpg", "rb") as f:
        response = client.post("/upload-image",
            files={"file": ("test_image.jpg", f, "image/jpeg")},
            headers={"Authorization": f"Bearer {user_token}"}
        )
    os.remove("test_image.jpg")
    assert response.status_code == 200
    assert "image_url" in response.json()

def test_upload_image_invalid_token():
    with open("test_image.jpg", "wb") as f:
        f.write(b"fake image content")
    with open("test_image.jpg", "rb") as f:
        response = client.post("/upload-image",
            files={"file": ("test_image.jpg", f, "image/jpeg")},
            headers={"Authorization": "Bearer invalidtoken"}
        )
    os.remove("test_image.jpg")
    assert response.status_code == 401

def test_create_plante(test_db, user_token, test_user):
    response = client.post("/plantes", json={
        "name": "Rose",
        "type": "Flower",
        "description": "A beautiful rose",
        "image_url": "/uploads/rose.jpg",
        "approuvee": False
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    assert response.json()["name"] == "Rose"
    assert response.json()["created_by"] == test_user.nom

def test_get_plantes(test_db, test_user):
    plante = Plante(
        name="Test Tree",
        type="Tree",
        description="Green test tree",
        image_url="/uploads/tree.jpg",
        approuvee=True,
        proprietaire_id=test_user.id
    )
    test_db.add(plante)
    test_db.commit()
    response = client.get("/plantes")
    assert response.status_code == 200
    assert any(p["name"] == "Test Tree" for p in response.json())

def test_propose_plante(user_token, test_user):
    response = client.post("/propositions", json={
        "name": "Mint",
        "type": "Herb",
        "description": "Fresh mint plant",
        "image_url": "/uploads/mint.jpg"
    }, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    assert response.json()["name"] == "Mint"
    assert response.json()["utilisateur_id"] == test_user.id

def test_admin_validate_proposition(test_db, admin_token, test_user):
    proposition = PropositionPlante(
        name="Sunflower",
        type="Flower",
        description="Bright yellow",
        image_url="/uploads/sunflower.jpg",
        utilisateur_id=test_user.id,
        statut="pending"
    )
    test_db.add(proposition)
    test_db.commit()
    response = client.post(
        f"/admin/propositions/{proposition.id}/valider",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["approuvee"] is True

# def test_admin_delete_user(client, admin_token_headers, test_user):
#     response = client.delete(
#         f"/users/{test_user.id}",
#         headers=admin_token_headers
#     )
#     assert response.status_code == 200


def test_get_notifications(test_db, test_user, user_token):
    notif = Notification(
        message="Plant approved!",
        type="PROPOSITION_VALIDEE",
        utilisateur_id=test_user.id
    )
    test_db.add(notif)
    test_db.commit()
    response = client.get("/notifications", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    assert any(n["type"] == "approved" for n in response.json())
