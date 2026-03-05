from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from .database import SessionLocal, engine
from .models import Base, User, Task, Issue
from .schemas import UserCreate, UserLogin, TaskCreate, IssueCreate, IssueUpdate
from .auth import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM

Base.metadata.create_all(bind=engine)
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth Dependency
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ----------------- AUTH -----------------
@app.post("/register", status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(email=user.email, password=hash_password(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"user_id": db_user.id, "role": db_user.role})
    return {"access_token": token, "token_type": "bearer"}

# ----------------- TASKS -----------------
@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    new_task = Task(title=task.title, description=task.description, owner_id=current_user["user_id"])
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

@app.get("/tasks")
def get_tasks(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return db.query(Task).filter(Task.owner_id == current_user["user_id"]).all()

# ----------------- ISSUES -----------------
@app.post("/issues", status_code=201)
def create_issue(issue: IssueCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    new_issue = Issue(title=issue.title, description=issue.description, owner_id=current_user["user_id"])
    db.add(new_issue)
    db.commit()
    db.refresh(new_issue)
    return new_issue

@app.get("/issues")
def get_issues(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    # If admin, show all
    if current_user["role"] == "admin":
        return db.query(Issue).all()
    # Else, user sees only their own
    return db.query(Issue).filter(Issue.owner_id == current_user["user_id"]).all()

@app.put("/issues/{issue_id}")
def update_issue(issue_id: int, update: IssueUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    issue.status = update.status
    db.commit()
    return {"message": "Issue updated"}