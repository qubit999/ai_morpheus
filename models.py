import os
from pydantic import BaseModel, EmailStr
from typing import List, Dict

class Message(BaseModel):
    role: str
    content: str

class RequestModel(BaseModel):
    messages: List[Message]
    model: str

class LoginUser(BaseModel):
    csrf_token: str
    email: EmailStr
    password: str
    submit: str

class CsrfSettings(BaseModel):
    secret_key: str = os.getenv("CSRF_SECRET_KEY")
    cookie_key: str = os.getenv("CSRF_COOKIE")