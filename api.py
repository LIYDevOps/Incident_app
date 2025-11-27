from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import HTTPException

app = FastAPI()

# In-memory "database" for demonstration purposes
users_db = {"test@example.com": {"username": "lakshman", "password": "mypassword"}}

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


@app.post("/signup")
def signup(data: SignUpData):
    if data.email in users_db:
        raise HTTPException(
            status_code=400,
            detail="Email already exists. Please login instead."
        )
    users_db[data.email] = {"username": data.username, "password": data.password}
    return {"message": "User signed up successfully", "user": data.username}

@app.post("/login")
def login(data: LoginData):
    if data.email not in users_db:
        raise HTTPException(status_code=404, detail="User not found. Please sign up.")
    if users_db[data.email]["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid password.")
    return {"message": "Login successful", "user": users_db[data.email]["username"]}