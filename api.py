from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import HTTPException

app = FastAPI()

# In-memory "database" for demonstration purposes
users_db = {"test@gmail.com": {"username": "lakshman", "password": "mypassword"}}

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the expected data structure
class SignUpData(BaseModel):
    username: str
    email: str
    password: str

class LoginData(BaseModel):
    email: str
    password: str

incidents_db = []

class IncidentData(BaseModel):
    title: str
    description: str
    status: str = "open"   # default status
    assigned_to: str       # email of user


@app.post("/signup")
def signup(data: SignUpData):
    if data.email in users_db:
        # User already exists
        return {
            "message": "User already exists. Please try login.",
            "redirect": "login"
        }
    # Create new user
    users_db[data.email] = {"username": data.username, "password": data.password}
    return {
        "message": "User signed up successfully",
        "user": data.username,
        "redirect": "login"  # after signup success, go to login
    }

@app.post("/login")
def login(data: LoginData):
    if data.email not in users_db:
        raise HTTPException(status_code=404, detail="User not found. Please sign up.")
    if users_db[data.email]["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid password.")
    return {"message": "Login successful", "user": users_db[data.email]["username"]}


@app.get("/me")
def get_user(email: str):
    user = users_db.get(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user["username"], "email": email}


@app.post("/incidents")
def create_incident(data: IncidentData):
    incident_id = len(incidents_db) + 1
    incident = {"id": incident_id, **data.dict()}
    incidents_db.append(incident)
    return {"message": "Incident created successfully", "incident": incident}

@app.get("/incidents")
def list_open_incidents(email: str):
    user_incidents = [i for i in incidents_db if i["assigned_to"] == email and i["status"] == "open"]
    return {"open_incidents": user_incidents, "total": len(user_incidents)}
