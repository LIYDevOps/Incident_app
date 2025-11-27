from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db import SessionLocal, User, Incident

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency: get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Schemas
class SignUpData(BaseModel):
    username: str
    email: str
    password: str

class LoginData(BaseModel):
    email: str
    password: str

class IncidentData(BaseModel):
    title: str
    description: str
    status: str = "open"
    assigned_to: str

# Signup
@app.post("/signup")
def signup(data: SignUpData, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if user:
        return {"message": "User already exists. Please try login.", "redirect": "login"}
    new_user = User(username=data.username, email=data.email, password=data.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User signed up successfully", "user": new_user.username, "redirect": "login"}

# Login
@app.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please sign up.")
    if user.password != data.password:
        raise HTTPException(status_code=401, detail="Invalid password.")
    return {"message": "Login successful", "user": user.username}

# Get user
@app.get("/me")
def get_user(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user.username, "email": user.email}

# Create incident
@app.post("/incidents")
def create_incident(data: IncidentData, db: Session = Depends(get_db)):
    incident = Incident(title=data.title, description=data.description,
                        status=data.status, assigned_to=data.assigned_to)
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return {"message": "Incident created successfully", "incident": incident.id}

# List incidents
@app.get("/incidents")
def list_open_incidents(email: str, db: Session = Depends(get_db)):
    incidents = db.query(Incident).filter(Incident.assigned_to == email, Incident.status == "open").all()
    return {"open_incidents": incidents, "total": len(incidents)}
