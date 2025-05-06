from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import timedelta, date
from . import models, database, auth
from .database import engine
from typing import Optional

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root(request: Request, current_user: Optional[models.User] = Depends(auth.get_current_user)):
    return templates.TemplateResponse("home.html", {"request": request, "current_user": current_user})

@app.get("/register")
def show_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(
    request: Request,
    name: str = Form(...),
    surname: str = Form(...),
    sex: str = Form(...),
    nationality: str = Form(...),
    organization_name: str = Form(...),
    job_title: str = Form(...),
    birthdate: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Check if email already exists
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Convert birthdate string to date object
    try:
        birthdate_obj = date.fromisoformat(birthdate)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Create new user
    hashed_password = auth.get_password_hash(password)
    user = models.User(
        name=name,
        surname=surname,
        sex=sex,
        nationality=nationality,
        organization_name=organization_name,
        job_title=job_title,
        birthdate=birthdate_obj,
        email=email,
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    
    return RedirectResponse(url="/login", status_code=303)

@app.get("/login")
def show_login(request: Request, error: str = None):
    return templates.TemplateResponse("login.html", {"request": request, "error": error})

@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Incorrect email or password"}
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=False,  # Set to True in production
        samesite="lax",
        max_age=1800  # 30 minutes in seconds
    )
    return response

@app.get("/users")
def show_users(
    request: Request,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    users = db.query(models.User).all()
    return templates.TemplateResponse(
        "users.html",
        {"request": request, "users": users, "current_user": current_user}
    )

@app.get("/profile")
def show_profile(
    request: Request,
    current_user: models.User = Depends(auth.get_current_user)
):
    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "current_user": current_user}
    )

@app.post("/profile")
async def update_profile(
    request: Request,
    name: str = Form(...),
    surname: str = Form(...),
    sex: str = Form(...),
    nationality: str = Form(...),
    organization_name: str = Form(...),
    job_title: str = Form(...),
    birthdate: str = Form(...),
    email: str = Form(...),
    current_password: str = Form(None),
    new_password: str = Form(None),
    confirm_password: str = Form(None),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Get a fresh copy of the user from the database
        user = db.query(models.User).filter(models.User.id == current_user.id).first()
        if not user:
            return templates.TemplateResponse(
                "profile.html",
                {
                    "request": request,
                    "current_user": current_user,
                    "error": "User not found"
                }
            )

        # Check if email is being changed to one that already exists
        if email != user.email:
            existing_user = db.query(models.User).filter(models.User.email == email).first()
            if existing_user:
                return templates.TemplateResponse(
                    "profile.html",
                    {
                        "request": request,
                        "current_user": current_user,
                        "error": "Email already registered"
                    }
                )

        # Convert birthdate string to date object
        try:
            birthdate_obj = date.fromisoformat(birthdate)
        except ValueError:
            return templates.TemplateResponse(
                "profile.html",
                {
                    "request": request,
                    "current_user": current_user,
                    "error": "Invalid date format. Use YYYY-MM-DD"
                }
            )

        # Update user information
        user.name = name
        user.surname = surname
        user.sex = sex
        user.nationality = nationality
        user.organization_name = organization_name
        user.job_title = job_title
        user.birthdate = birthdate_obj
        user.email = email
        
        # Update password if provided
        if current_password and new_password and confirm_password:
            if not auth.verify_password(current_password, user.hashed_password):
                return templates.TemplateResponse(
                    "profile.html",
                    {
                        "request": request,
                        "current_user": current_user,
                        "error": "Current password is incorrect"
                    }
                )
            if new_password != confirm_password:
                return templates.TemplateResponse(
                    "profile.html",
                    {
                        "request": request,
                        "current_user": current_user,
                        "error": "New passwords do not match"
                    }
                )
            user.hashed_password = auth.get_password_hash(new_password)
        
        db.commit()
        return RedirectResponse(url="/profile", status_code=303)
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "current_user": current_user,
                "error": f"An error occurred: {str(e)}"
            }
        )

@app.get("/logout")
def logout(request: Request):
    token = request.cookies.get("access_token")
    if token and token.startswith("Bearer "):
        auth.revoke_token(token[7:])  # Remove "Bearer " prefix
    
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response

@app.post("/delete-account")
async def delete_account(
    request: Request,
    confirm_password: str = Form(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if not auth.verify_password(confirm_password, current_user.hashed_password):
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "current_user": current_user,
                "error": "Incorrect password"
            }
        )
    
    try:
        # Get a fresh copy of the user from the database
        user_to_delete = db.query(models.User).filter(models.User.id == current_user.id).first()
        if not user_to_delete:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete the user
        db.delete(user_to_delete)
        db.commit()
        
        # Clear the session
        response = RedirectResponse(url="/", status_code=303)
        response.delete_cookie("access_token")
        return response
    except Exception as e:
        db.rollback()
        return templates.TemplateResponse(
            "profile.html",
            {
                "request": request,
                "current_user": current_user,
                "error": f"An error occurred while deleting your account: {str(e)}"
            }
        )