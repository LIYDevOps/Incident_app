# app.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import joblib
import datetime
import pandas as pd

from db_config import Base, engine, SessionLocal, User, Group, GroupMembership, Incident, IncidentJournal

# Create tables if not exist
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict to http://localhost:8501 later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Load model if available
try:
    MODEL = joblib.load("resolution_model.pkl")
except Exception:
    MODEL = None

# Schemas
class SignUpData(BaseModel):
    username: str
    email: str
    password: str
    role: str = "user"

class LoginData(BaseModel):
    email: str
    password: str

class IncidentCreate(BaseModel):
    title: str
    description: str
    group_name: str

class AssignIncident(BaseModel):
    analyst_email: str

class UpdateIncident(BaseModel):
    status: str
    comment: str

class PredictRequest(BaseModel):
    title: str
    description: str
    group: str
    type: str

# Utilities
def serialize_incident(i: Incident):
    return {
        "id": i.id,
        "title": i.title,
        "description": i.description,
        "status": i.status,
        "requester_id": i.requester_id,
        "assigned_group_id": i.assigned_group_id,
        "assigned_to_user_id": i.assigned_to_user_id,
        "created_at": i.created_at,
        "updated_at": i.updated_at,
        "closed_at": i.closed_at,
        "group": i.assigned_group.name if i.assigned_group else None,
        "assigned_to": i.assigned_to.email if i.assigned_to else None,
    }

def serialize_journal(j: IncidentJournal):
    return {
        "id": j.id,
        "author": j.author.email,
        "comment": j.comment,
        "status": j.status,
        "created_at": j.created_at,
    }

def infer_type(title, description):
    text = f"{title} {description}".lower()
    if "network" in text or "vpn" in text or "wifi" in text:
        return "Network"
    if "server" in text or "database" in text or "db" in text:
        return "Infra"
    if "bug" in text or "error" in text or "ui" in text or "app" in text:
        return "Software"
    return "General"

# Auth
@app.post("/signup")
def signup(data: SignUpData, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="User already exists")
    u = User(username=data.username, email=data.email, password=data.password, role=data.role)
    db.add(u); db.commit(); db.refresh(u)
    return {"message": "User signed up", "user": u.username, "role": u.role}

@app.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.email == data.email).first()
    if not u or u.password != data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful", "user": u.username, "role": u.role}

# Groups
@app.post("/groups/create")
def create_group(name: str, db: Session = Depends(get_db)):
    g = db.query(Group).filter(Group.name == name).first()
    if g:
        return {"message": "Group already exists", "group_id": g.id}
    g = Group(name=name); db.add(g); db.commit(); db.refresh(g)
    return {"message": "Group created", "group_id": g.id}

@app.post("/groups/add_analyst")
def add_analyst_to_group(analyst_email: str, group_name: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == analyst_email, User.role == "analyst").first()
    if not user:
        raise HTTPException(status_code=404, detail="Analyst not found or not an analyst")
    group = db.query(Group).filter(Group.name == group_name).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    if db.query(GroupMembership).filter_by(user_id=user.id, group_id=group.id).first():
        return {"message": "Analyst already in group"}
    m = GroupMembership(user_id=user.id, group_id=group.id); db.add(m); db.commit()
    return {"message": "Analyst added to group"}

# Incidents
@app.post("/incidents")
def create_incident(data: IncidentCreate, requester_email: str, db: Session = Depends(get_db)):
    requester = db.query(User).filter(User.email == requester_email).first()
    if not requester:
        raise HTTPException(status_code=404, detail="Requester not found")
    group = db.query(Group).filter(Group.name == data.group_name).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    now = datetime.datetime.now(datetime.timezone.utc)
    inc = Incident(
        title=data.title, description=data.description, status="open",
        requester_id=requester.id, assigned_group_id=group.id,
        assigned_to_user_id=None, created_at=now, updated_at=now
    )
    db.add(inc); db.commit(); db.refresh(inc)

    # Optional: immediate prediction and store in journal for user visibility
    predicted_hours = None
    if MODEL:
        ptype = infer_type(inc.title, inc.description)
        X = [{"title": inc.title, "description": inc.description, "group": group.name, "type": ptype}]
        try:
            predicted_hours = float(MODEL.predict(X)[0])
            j = IncidentJournal(
                incident_id=inc.id, author_user_id=requester.id,
                comment=f"Projected resolution: {predicted_hours:.1f} hours", status="open",
                created_at=now
            )
            db.add(j); db.commit()
        except Exception:
            pass

    return {"message": "Incident created", "incident": serialize_incident(inc), "predicted_hours": predicted_hours}

@app.get("/incidents/my")
def my_incidents(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    incs = db.query(Incident).filter(Incident.requester_id == user.id).order_by(Incident.id.desc()).all()
    return {"incidents": [serialize_incident(i) for i in incs]}

@app.get("/incidents/group_queue")
def group_queue(group_name: str, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.name == group_name).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    incs = db.query(Incident).filter(
        Incident.assigned_group_id == group.id,
        Incident.assigned_to_user_id.is_(None),
        Incident.status == "open"
    ).order_by(Incident.id.asc()).all()
    return {"open_incidents": [serialize_incident(i) for i in incs]}

@app.post("/incidents/{incident_id}/assign")
def assign_incident(incident_id: int, data: AssignIncident, db: Session = Depends(get_db)):
    analyst = db.query(User).filter(User.email == data.analyst_email, User.role == "analyst").first()
    if not analyst:
        raise HTTPException(status_code=404, detail="Analyst not found or not an analyst")
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    membership = db.query(GroupMembership).filter_by(user_id=analyst.id, group_id=inc.assigned_group_id, is_active=True).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Analyst not a member of group")

    inc.assigned_to_user_id = analyst.id
    inc.status = "assigned"
    inc.updated_at = datetime.datetime.now(datetime.timezone.utc)
    db.add(inc)
    j = IncidentJournal(
        incident_id=inc.id, author_user_id=analyst.id,
        comment=f"Assigned to {analyst.email}", status=inc.status,
        created_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(j); db.commit(); db.refresh(inc)
    return {"message": "Incident assigned", "incident": serialize_incident(inc)}

@app.get("/incidents/assigned")
def assigned_incidents(email: str, db: Session = Depends(get_db)):
    analyst = db.query(User).filter(User.email == email, User.role == "analyst").first()
    if not analyst:
        raise HTTPException(status_code=404, detail="Analyst not found or not an analyst")

    incs = db.query(Incident).filter(Incident.assigned_to_user_id == analyst.id).order_by(Incident.id.desc()).all()
    return {"assigned_incidents": [serialize_incident(i) for i in incs]}

@app.post("/incidents/{incident_id}/update")
def update_incident(incident_id: int, data: UpdateIncident, author_email: str, db: Session = Depends(get_db)):
    author = db.query(User).filter(User.email == author_email).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    valid = {"assigned", "in-progress", "resolved", "closed"}
    if data.status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {sorted(list(valid))}")

    now = datetime.datetime.now(datetime.timezone.utc)
    inc.status = data.status
    inc.updated_at = now
    if data.status == "closed":
        inc.closed_at = now

    j = IncidentJournal(incident_id=inc.id, author_user_id=author.id, comment=data.comment, status=data.status, created_at=now)
    db.add(j); db.add(inc); db.commit(); db.refresh(inc)
    return {"message": "Incident updated", "incident": serialize_incident(inc)}

@app.get("/incident/{incident_id}")
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    journals = db.query(IncidentJournal).filter(IncidentJournal.incident_id == inc.id).order_by(IncidentJournal.created_at.asc()).all()
    return {"incident": serialize_incident(inc), "journals": [serialize_journal(j) for j in journals]}

# Prediction endpoint (usable by Streamlit)
@app.post("/predict_resolution_time")
def predict_resolution(req: PredictRequest):
    if MODEL is None:
        raise HTTPException(status_code=503, detail="Model not loaded. Train it first.")
    X = pd.DataFrame([{"title": req.title, "description": req.description, "group": req.group, "type": req.type}])
    try:
        y = float(MODEL.predict(X)[0])
        return {"predicted_resolution_hours": y}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")


# Utility: get user stats for dashboard card
@app.get("/dashboard_stats")
def dashboard_stats(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    my_incs = db.query(Incident).filter(Incident.requester_id == user.id).all()
    open_count = sum(1 for i in my_incs if i.status != "closed")
    latest = my_incs[-1] if my_incs else None
    proj_hours = None
    if latest and MODEL:
        ptype = infer_type(latest.title, latest.description)
        try:
            proj_hours = float(MODEL.predict([{
                "title": latest.title, "description": latest.description,
                "group": latest.assigned_group.name if latest.assigned_group else "Unknown",
                "type": ptype
            }])[0])
        except Exception:
            proj_hours = None
    return {"open_incidents": open_count, "latest_projected_hours": proj_hours}
