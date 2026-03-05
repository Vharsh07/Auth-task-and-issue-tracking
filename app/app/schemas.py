from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None

class IssueCreate(BaseModel):
    title: str
    description: Optional[str] = None

class IssueUpdate(BaseModel):
    status: str