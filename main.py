"""
Main module for the FastAPI application.

This module sets up the FastAPI application, including middleware, routes, and configurations.
It imports necessary libraries and modules, including custom controllers, database handlers, helpers, and models.

Imports:
    - FastAPI and related modules for building the API.
    - CsrfProtect for CSRF protection.
    - Various response classes for handling different types of HTTP responses.
    - Jinja2Templates for template rendering.
    - StaticFiles for serving static files.
    - OAuth2PasswordBearer and OAuth2PasswordRequestForm for OAuth2 authentication.
    - Standard libraries such as os, json, datetime, and logging.
    - Third-party libraries such as jwt for JSON Web Token handling and passlib for password hashing.
    - Pydantic for data validation and settings management.
    - dotenv for loading environment variables from a .env file.
    - Custom modules for controllers, database interactions, helpers, and models.

Logging:
    Configures logging to output debug level messages.

Environment:
    Loads environment variables from a .env file.

Custom Modules:
    Imports custom modules for controllers, database interactions, helpers, and models.
"""

from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os
import json
from bson import ObjectId
from bson.json_util import JSONOptions 
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from jwt import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import Optional
import logging

logging.basicConfig(level=logging.DEBUG)

from dotenv import load_dotenv
load_dotenv()

# own classes:
from controller import *
from database import *
from helper import *
from models import *
# end own classes

controller = Controller()
templates = Jinja2Templates(directory="templates")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

class CsrfSettings(BaseSettings):
    secret_key: str = os.getenv("CSRF_SECRET_KEY")

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, csrf_protect: CsrfProtect = Depends()):
    csrf_token = csrf_protect.generate_csrf_tokens()
    current_user = await controller.get_current_active_user(request.cookies.get("access_token"))
    return templates.TemplateResponse("index.html", {"request": request, "title": "Index", "current_user": current_user, "csrf_token": csrf_token})

@app.get("/register", response_class=HTMLResponse)
async def register(request: Request, csrf_protect: CsrfProtect = Depends()):
    csrf_token = csrf_protect.generate_csrf_tokens()
    current_user = await controller.get_current_active_user(request.cookies.get("access_token"))
    response = templates.TemplateResponse("register.html", {"request": request, "title": "Register", "csrf_token": csrf_token, "current_user": current_user})
    csrf_protect.set_csrf_cookie(csrf_signed_token=csrf_token, response=response)
    return response

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request, csrf_protect: CsrfProtect = Depends()):
    csrf_token = csrf_protect.generate_csrf_tokens()
    current_user = await controller.get_current_active_user(request.cookies.get("access_token"))
    response = templates.TemplateResponse("login.html", {"request": request, "title": "Login", "csrf_token": csrf_token, "current_user": current_user})
    csrf_protect.set_csrf_cookie(csrf_signed_token=csrf_token, response=response)
    return response

@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request, response: HTMLResponse):
    response = RedirectResponse(url="/")
    response.set_cookie(key="access_token", path="/", value="", httponly=True, secure=True, samesite="Strict", expires=0)
    response.delete_cookie(key="access_token", path="/")
    return response

@app.get("/account", response_class=HTMLResponse)
async def account(request: Request, csrf_protect: CsrfProtect = Depends()):
    csrf_token = csrf_protect.generate_csrf_tokens()
    current_user = await controller.get_current_user(request.cookies.get("access_token"))
    print(current_user)
    response = templates.TemplateResponse("account.html", {"request": request, "title": "Account", "current_user": current_user, "csrf_token": csrf_token})
    return response

@app.post("/token")
async def login_for_access_token(
    #form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    response: JSONResponse, 
    request: Request,
    csrf_protect: CsrfProtect = Depends(),
):
    csrf_protect.validate_csrf(request)
    form_data = await request.form()
    if not form_data.get("email") or not form_data.get("password"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await controller.authenticate_user(form_data.get("email"), form_data.get("password"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=float(ACCESS_TOKEN_EXPIRE_MINUTES or 15.0))
    access_token = await controller.create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    response.headers["HX-Redirect"] = "/"
    response.set_cookie(
        key="access_token",
        path="/",
        value=f"{access_token}",
        httponly=False,
        secure=True,
        samesite="Strict",
        expires=datetime.now(timezone.utc) + access_token_expires,
    )
    #return Token(access_token=access_token, token_type="bearer")
    await controller.update_user(email=user["email"], user={"last_login": datetime.now(timezone.utc), "last_ip": request.client.host}, current_user=access_token)
    return {"message": "Logged in"}


@app.get("/users/me/", response_class=JSONResponse)
async def read_users_me(
    token: Annotated[str, Depends(controller.oauth2_scheme)],
):
    result = await controller.get_current_user(token)
    return JSONTools(result).clean_json

@app.get("/users/me/items/", response_class=JSONResponse)
async def read_own_items(
    token: Annotated[str, Depends(controller.oauth2_scheme)],
):
    current_user = await controller.get_current_user(token)
    return {"item_id": "Foo", "owner": current_user}

@app.post("/users/create/", response_class=JSONResponse)
async def create_user(user: UserInDB, request: Request, response: JSONResponse, csrf_protect: CsrfProtect = Depends()):
    csrf_protect.validate_csrf(request)
    ip = request.client.host
    result = await controller.create_user(user, ip)
    if result is not Exception and result is not False:
        response.headers["HX-Redirect"] = "/login"
        return {"message": "User created"} # "user": str(result)
    elif result is not Exception and result is False:
        return {"message": "User already exists"}
    elif result is Exception:
        return {"message": str(result)}
    
@app.post("/user/disable", response_class=JSONResponse)
async def disable_user(user: UserInDB, token: Annotated[str, Depends(controller.oauth2_scheme)]):
    result = await controller.disable_user(user=user, current_user=token)
    if result is not Exception and result is not False:
        return {"message": "User disabled"}
    elif result is Exception:
        return {"message": str(result)}
    elif result is False:
        return {"message": "Wrong password"}
    
@app.post("/user/update/", response_class=JSONResponse)
async def update_user(request: Request, token: Annotated[str, Depends(controller.oauth2_scheme)], csrf_protect: CsrfProtect = Depends()):
    csrf_protect.validate_csrf(csrf_protect)
    request = await request.json()
    result = await controller.update_user(email=request.get("email"), user=request, current_user=token)
    if result is not Exception and result is not False:
        return {"message": "User updated"}
    elif result is Exception:
        return {"message": str(result)}
    elif result is False:
        return {"message": "Unauthorized"}

@app.post("/models/get", response_class=JSONResponse)
async def get_models(token: Annotated[str, Depends(controller.oauth2_scheme)], csrf_protect: CsrfProtect = Depends()):
    csrf_protect.validate_csrf(csrf_protect)
    result = await controller.get_models(current_user=token)
    if result is not Exception and result is not False:
        return result
    elif result is Exception:
        return {"message": str(result)}
    elif result is False:
        return {"message": "Unauthorized"}    

@app.post("/model/response", response_class=JSONResponse)
async def get_response(request: RequestModel, token: Annotated[str, Depends(controller.oauth2_scheme)], csrf_protect: CsrfProtect = Depends()):
    csrf_protect.validate_csrf(csrf_protect)
    messages = request.messages
    model = request.model
    if messages is not None:
        messages = [message.model_dump() for message in request.messages]

    result = await controller.get_response(messages, model, current_user=token)

    if result is not Exception and result is not False:
        return result
    elif result is Exception:
        return {"message": str(result)}
    elif result is False:
        return {"message": "Unauthorized"}

@app.post("/model/streaming_response", response_class=StreamingResponse)
async def get_response(request: Request, token: Annotated[str, Depends(controller.oauth2_scheme)], csrf_protect: CsrfProtect = Depends()):
    csrf_protect.validate_csrf(csrf_protect)

    request_data = await request.json()
    messages = request_data.get("messages")
    model = request_data.get("model")
    advanced = request_data.get("advanced")
    async def event_stream():
        async for delta in controller.get_streaming_response(messages, model, advanced, current_user=token):
            try:
                #json_data = JSONTools(delta).convert_to_json()
                #result = JSONTools(json_data).clean_json
                #logging.debug("data: %s \n\n", delta)
                yield f"data: {delta} \n\n\n\n"
            except Exception as e:
                logging.error(f"Error processing delta: {delta}, Error: {e}")

    return StreamingResponse(event_stream(), media_type="text/event-stream")
    
@app.post("/threads/create/", response_class=JSONResponse)
async def create_thread(thread: Thread, token: Annotated[str, Depends(controller.oauth2_scheme)]):
    result = await controller.create_thread(thread, current_user=token)
    if result is not Exception and result is not False:
        return {"message": "Thread created"}
    
@app.get("/threads/get/all", response_class=JSONResponse)
async def get_threads(token: Annotated[str, Depends(controller.oauth2_scheme)]):
    result = await controller.get_threads(current_user=token)
    if result is not Exception and result is not False:
        return JSONTools(result).clean_json
    elif result is Exception:
        return {"message": str(result)}
    elif result is False:
        return {"message": "Unauthorized"}

"""
@app.post("/threads/update/", response_class=JSONResponse)
async def update_thread(thread: Thread, token: Annotated[str, Depends(controller.oauth2_scheme)]):
    result = await controller.update_thread(thread, current_user=token)
    if result is not Exception and result is not False:
        return {"message": "Thread updated"}
    elif result is Exception:
        return {"message": str(result)}
    elif result is False:
        return {"message": "Unauthorized"}
"""
    
@app.get("/threads/get/{thread_id}", response_class=JSONResponse)
async def get_thread(thread_id: str, token: Annotated[str, Depends(controller.oauth2_scheme)]):
    result = await controller.get_thread(thread_id, current_user=token)
    if result is not Exception and result is not False:
        return JSONTools(result).clean_json
    elif result is Exception:
        return {"message": str(result)}
    elif result is False:
        return {"message": "Unauthorized"}
    
@app.post("/threads/get/{thread_id}/add_message", response_class=JSONResponse)
async def add_message_to_thread(thread_id: str, message: str, token: Annotated[str, Depends(controller.oauth2_scheme)]):
    result = await controller.add_message_to_thread(thread_id=thread_id, message=message, current_user=token)
    if result is not Exception and result is not False:
        return {"message": "Message added"}
    elif result is Exception:
        return {"message": str(result)}
    elif result is False:
        return {"message": "Unauthorized"}
    
@app.post("/threads/get/{thread_id}/messages", response_class=JSONResponse)
async def get_messages_from_thread(thread_id: str, token: Annotated[str, Depends(controller.oauth2_scheme)]):
    result = await controller.get_messages_from_thread(thread_id=thread_id, current_user=token)
    if result is not Exception and result is not False:
        return JSONTools(result).clean_json
    elif result is Exception:
        return {"message": str(result)}
    elif result is False:
        return {"message": "Unauthorized"}
    
@app.post("/threads/get/{thread_id}/disable", response_class=JSONResponse)
async def disable_thread(thread_id: str, token: Annotated[str, Depends(controller.oauth2_scheme)]):
    result = await controller.disable_thread(thread_id=thread_id, current_user=token)
    if result is not Exception and result is not False:
        return JSONTools(result).clean_json
    elif result is Exception:
        return {"message": str(result)}
    elif result is False:
        return {"message": "Unauthorized"}
    
@app.get("/settings/get", response_class=JSONResponse)
async def get_settings(token: Annotated[str, Depends(controller.oauth2_scheme)]):
    result = await controller.get_setting(current_user=token)
    if result is not Exception and result is not False:
        return JSONTools(result).clean_json
    elif result is Exception:
        return {"message": str(result)}
    elif result is False:
        return {"message": "Unauthorized"}
    
@app.post("/settings/update", response_class=JSONResponse)
async def update_settings(settings: Setting, token: Annotated[str, Depends(controller.oauth2_scheme)]):
    result = await controller.update_setting(settings, current_user=token)
    if result is not Exception and result is not False:
        return {"message": "Settings updated"}
    elif result is Exception:
        return {"message": str(result)}
    elif result is False:
        return {"message": "Unauthorized"}

if __name__ == "__main__":
    import uvicorn
    print("http://127.0.0.1:8000/")
    uvicorn.run(app, host="0.0.0.0", port=8000)