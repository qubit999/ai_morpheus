import os
from datetime import datetime, timedelta, timezone
import time
from typing import Annotated
from bson import ObjectId, json_util
import jwt
from jwt import InvalidTokenError
import asyncio
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel
import logging
logging.getLogger('passlib').setLevel(logging.ERROR)

from dotenv import load_dotenv
load_dotenv()

from database import Database, User, UserInDB, Thread, Payment, Setting
from ai import *
from helper import *
from models import *

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class QueryParams:
    def make_bool(self, value):
        return not(value == "False" or value == "false" or value == "0" or value == 0 or value == False)

    def __init__(self, boolable: str):
        self.boolable = self.make_bool(boolable)

class Controller:

    def __init__(self):
        self.db = Database()
        self.ai = AI()
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.SECRET_KEY = os.getenv("SECRET_KEY")
        self.ALGORITHM = os.getenv("ALGORITHM")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

    async def verify_password(self, plain_password, password1):
        return self.pwd_context.verify(plain_password, password1)

    async def get_password_hash(self, password):
        return self.pwd_context.hash(password)

    async def authenticate_user(self, email: str, password: str):
        user = await self.db.get_user(email=email)
        if not user:
            return False
        if not await self.verify_password(password, user["password1"]):
            return False
        if isinstance(user, dict):
            user = {k: str(v) if isinstance(v, ObjectId) else v for k, v in user.items()}
        return user

    async def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15.0)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt

    async def get_current_user(self, token: Annotated[str, Depends()]):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM or "HS256"])
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
            token_data = TokenData(username=email)
        except InvalidTokenError:
            raise credentials_exception
        user = await self.db.get_user(email=token_data.username)
        exclude_list = ["password1", "password2", "disabled", "registration_ip", "registration_date", "last_login", "last_ip", "_id", "role"]
        for key in exclude_list:
            if key in user:
                user.pop(key)
        if user is None:
            raise credentials_exception
        return user

    async def get_current_active_user(self, token: Annotated[User, Depends(get_current_user)]):
        if token is None or token == "":
            return False
        payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM or "HS256"])
        email: str = payload.get("sub")
        if email is None:
            return False
        token_data = TokenData(username=email)
        return token_data
    
    async def create_user(self, user: UserInDB, ip: str):
        user.registration_date = datetime.now(timezone.utc)
        user.registration_ip = ip
        user = UserInDB(**user.model_dump(exclude={"password1"}), password1=await self.get_password_hash(user.password1))
        return await self.db.create_user(user)
    
    async def update_user(self, email, user, current_user: Annotated[str, Depends(get_current_user)]):
        jwt_user = await self.get_current_user(current_user)
        if jwt_user["email"] != email:
            return False
        user_ = await self.db.get_user(email=email)
        user_dict = {k: v for k, v in user.items() if k not in ["disabled", "registration_ip", "registration_date", "csrf_token"]}
        for key, value in user_dict.items():
            if key == "_id":
                continue
            else:
                result = await self.db.update_user(email=email, field=key, value=user_dict[key])
                print(result)
    
    async def disable_user(self, user: UserInDB, current_user: Annotated[str, Depends(get_current_user)]):
        jwt_user = await self.get_current_user(current_user)
        if jwt_user["username"] != user.username:
            return False
        user_ = self.db.get_user(username=user.username)
        if await self.verify_password(user.password1, user_["password1"]):
            await self.db.update_user(username=user.username, field="disabled", value=True)
    
    async def get_response(self, messages: List, model: str, current_user: Annotated[str, Depends(get_current_user)]):
        jwt_user = await self.get_current_user(current_user)
        response = await self.ai.get_response(messages=messages, model=model)
        return response

    async def get_streaming_response(self, messages: List, model: str, advanced: str, current_user: Annotated[str, Depends(get_current_user)]):
        jwt_user = await self.get_current_user(current_user)
        if advanced == "true":
            async for delta in self.ai.get_stream_response(messages=messages, model=model):
                if delta is not None:
                    yield delta
        else:
            async for delta in self.ai.get_stream_response_no_advanced(messages=messages, model=model):
                if delta is not None:
                    yield delta

    async def get_models(self, current_user: Annotated[str, Depends(get_current_user)]):
        jwt_user = await self.get_current_user(current_user)
        return await self.ai.get_models()
                
    async def create_thread(self, thread: Thread, current_user: Annotated[str, Depends(get_current_user)]):
        jwt_user = await self.get_current_user(current_user)
        thread.thread_id = jwt_user["username"] + str(time.time())
        thread.title = str(datetime.now(timezone.utc))
        thread.created_by = jwt_user["username"]
        thread.last_updated = datetime.now(timezone.utc)
        return await self.db.create_thread(Thread(**thread.model_dump()))

    async def get_threads(self, current_user: Annotated[str, Depends(get_current_user)]):
        jwt_user = await self.get_current_user(current_user)
        return await self.db.get_threads(created_by=jwt_user["username"])
    
    async def get_thread(self, thread_id: str, current_user: Annotated[str, Depends(get_current_user)]):
        jwt_user = await self.get_current_user(current_user)
        return await self.db.get_threads(thread_id=thread_id, created_by=jwt_user["username"])

    """
    async def update_thread(self, thread: Thread, current_user: Annotated[str, Depends(get_current_user)]):
        jwt_user = await self.get_current_user(current_user)
        thread.created_by = jwt_user["username"]
        thread.last_updated = datetime.now(timezone.utc)
        thread.title = str(thread.last_updated)
        for key, value in thread.model_dump().items():
            if key == "created_by" or key == "created_at" or key == "thread_id":
                continue
            await self.db.update_thread(created_by=jwt_user["username"], field=key, value=value)
    """

    async def disable_thread(self, thread_id: str, current_user: Annotated[str, Depends(get_current_user)]):
        jwt_user = await self.get_current_user(current_user)
        thread_username = await self.db.get_threads(thread_id=thread_id, created_by=jwt_user["username"])["created_by"]
        if thread_username != jwt_user["username"]:
            raise HTTPException(status_code=403, detail="Not authorized to disable this thread")
        return await self.db.update_thread(thread_id=thread_id, field="disabled", value=True)
    
    async def add_message_to_thread(self, thread_id: str, message: str, current_user: Annotated[str, Depends(get_current_user)]):
        jwt_user = await self.get_current_user(current_user)
        timestamp = datetime.now(timezone.utc)
        await self.db.update_thread(thread_id=thread_id, field="last_updated", value=timestamp)
        await self.db.update_thread(thread_id=thread_id, field="title", value=str(timestamp))
        return await self.db.add_message_to_thread(thread_id, message, jwt_user["username"])
    
    async def get_messages_from_thread(self, thread_id: str, current_user: Annotated[str, Depends(get_current_user)]):
        jwt_user = await self.get_current_user(current_user)
        return await self.db.get_thread_messages(thread_id=thread_id, created_by=jwt_user["username"])
    
    async def get_setting(self, current_user: Annotated[str, Depends(get_current_user)]):
        jwt_user = await self.get_current_user(current_user)
        return await self.db.get_setting(created_by=jwt_user["username"])
    
    async def update_setting(self, setting: Setting, current_user: Annotated[str, Depends(get_current_user)]):
        jwt_user = await self.get_current_user(current_user)
        return await self.db.update_setting(created_by=jwt_user["username"], field=setting.key, value=setting.value)
    
if __name__ == "main":
    controller = Controller()
    controller.get_response({"messages": [{"role": "user", "content": "Hello, how are you?"}], "model": "llama3.1:8b"}, "token")