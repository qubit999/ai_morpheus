import os
from pydantic import BaseModel, EmailStr
from typing import List, Dict

class Message(BaseModel):
    """
    Represents a message with a role and content.

    Attributes:
        role (str): The role of the message sender (e.g., user, system).
        content (str): The content of the message.
    """
    role: str
    content: str

class RequestModel(BaseModel):
    """
    Represents a request model containing a list of messages and a model identifier.

    Attributes:
        messages (List[Message]): A list of Message objects.
        model (str): The identifier of the model to be used.
    """
    messages: List[Message]
    model: str

class LoginUser(BaseModel):
    """
    Represents a login user with CSRF token, email, password, and submit action.

    Attributes:
        csrf_token (str): The CSRF token for the session.
        email (EmailStr): The email address of the user.
        password (str): The password of the user.
        submit (str): The submit action.
    """
    csrf_token: str
    email: EmailStr
    password: str
    submit: str

class CsrfSettings(BaseModel):
    """
    Represents CSRF settings with secret key and cookie key.

    Attributes:
        secret_key (str): The secret key for CSRF protection.
        cookie_key (str): The cookie key for CSRF protection.
    """
    secret_key: str = os.getenv("CSRF_SECRET_KEY")
    cookie_key: str = os.getenv("CSRF_COOKIE")