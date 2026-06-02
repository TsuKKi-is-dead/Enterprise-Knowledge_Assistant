from pydantic import BaseModel
from typing import List, Optional

class User(BaseModel):
    email: str
    password: str
    role: str = "employee"

class Token(BaseModel):
    access_token: str
    token_type: str

class Query(BaseModel):
    question: str

class DocumentUpload(BaseModel):
    filename: str