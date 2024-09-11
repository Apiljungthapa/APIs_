from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# FastAPI instance
app = FastAPI()

# HTML Templates for rendering login and role-based pages
templates = Jinja2Templates(directory="templates")  # Ensure templates directory is correct

# JWT Configuration
SECRET_KEY = "your_secret_key"  # Replace with a secure key
ALGORITHM = "HS256"  # Algorithm used for encoding and decoding JWT tokens
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # JWT token expiry time in minutes

# OAuth2 configuration for extracting token from requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# In-memory fake database for demonstration purposes
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "password": "adminpassword",  # Plain text password for simplicity
        "disabled": False,
        "role": "admin"
    },
    "testuser": {
        "username": "testuser",
        "full_name": "Test User",
        "email": "testuser@example.com",
        "password": "userpassword",  # Plain text password for simplicity
        "disabled": False,
        "role": "user"
    }
}

# Pydantic models for data validation and serialization

class Token(BaseModel):
    """Model for JWT token response."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Model for JWT token payload (data inside the token)."""
    username: Optional[str] = None

class User(BaseModel):
    """Model for the user."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None
    role: str

class UserInDB(User):
    """Model for the user stored in the database."""
    password: str
    
@app.get("/", response_class=HTMLResponse)
async def welcome(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})
   

# Helper Functions for Authentication

def get_user(db, username: str) -> Optional[UserInDB]:
    """Retrieves a user from the database by username."""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)  # Use Pydantic model to ensure data integrity

def authenticate_user(fake_db, username: str, password: str, role: str) -> Optional[UserInDB]:
    """Authenticates a user by verifying the provided username, password, and role."""
    user = get_user(fake_db, username)
    if not user or user.role != role:
        return None
    if user.password != password:  # Simple plain text password check
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT token with a specified expiration time."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})  # Add expiration time to the token payload
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependency to get the current user from the JWT token

async def get_current_user(request: Request) -> User:
    """Retrieves the current user based on the JWT token provided in the request."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        token = token.split(" ")[1]  # Remove "Bearer" part
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")  # Extract 'sub' (subject) from token payload
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        token_data = TokenData(username=username)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    return user

# Dependency to check if the current user is active

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Checks if the current user is active."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Utility Function to Redirect Admins Back to the Admin Page

async def redirect_admin_to_admin_page(request: Request, current_user: User) -> Optional[RedirectResponse]:
    """Redirect admin users back to the admin page if they try to access non-admin pages."""
    if current_user.role == "admin" and request.url.path != "/admin":
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    return None

# Dependency to check if the current user is an admin

async def get_current_admin_user(request: Request, current_user: User = Depends(get_current_active_user)) -> User:
    """Checks if the current user has an admin role and handles redirects for non-admins."""
    redirect_response = await redirect_admin_to_admin_page(request, current_user)
    if redirect_response:
        return redirect_response

    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    
    return current_user

async def get_current_user_role(request: Request, current_user: User = Depends(get_current_active_user)) -> User:
    """Checks if the current user has a 'user' role."""
    if current_user.role != "user":
        # Redirect back to admin page if the user is admin
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    return current_user

# Updated Login Endpoint to handle role-based redirection

@app.post("/login", response_class=HTMLResponse)
async def login_for_access_token(request: Request, username: str = Form(...), password: str = Form(...), role: str = Form(...)):
    """Endpoint for user login that returns a JWT token and redirects based on role."""
    user = authenticate_user(fake_users_db, username, password, role)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials or role!"})

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )

    # Redirect based on role
    if user.role == "admin":
        response = RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    else:
        response = RedirectResponse(url="/user", status_code=status.HTTP_302_FOUND)
    
    # Set JWT token in a cookie
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

# Role-Based Protected Endpoints

@app.get("/admin", response_class=HTMLResponse)
async def read_admin_dashboard(request: Request, current_user: User = Depends(get_current_admin_user)):
    """Protected endpoint accessible only to users with the 'admin' role."""
    if isinstance(current_user, RedirectResponse):  # If redirected, return response
        return current_user
    return templates.TemplateResponse("admin.html", {"request": request, "user": current_user})

@app.get("/user", response_class=HTMLResponse)
async def read_user_dashboard(request: Request, current_user: User = Depends(get_current_user_role)):
    """Protected endpoint accessible to all authenticated and active users."""
    # Check if the returned object is a redirect response
    if isinstance(current_user, RedirectResponse):
        return current_user  # Return the redirect response if not authorized

    # Check if the user is admin, redirect them back to admin route
    if current_user.role == "admin":
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse("user.html", {"request": request, "user": current_user})

# Public Login Form Endpoint

@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    """Public endpoint that serves the login form."""
    return templates.TemplateResponse("login.html", {"request": request})

# Extra Endpoint for demonstration purposes
@app.get("/extra", response_class=HTMLResponse)
async def read_extra_page(request: Request, current_user: User = Depends(get_current_active_user)):
    """Public endpoint for an extra page."""
    
    # Check if the user is admin and redirect if needed
    redirect_response = await redirect_admin_to_admin_page(request, current_user)
    if redirect_response:
        return redirect_response

    return templates.TemplateResponse("extra.html", {"request": request, "user": current_user})

# Example of another endpoint that would require the same check
@app.get("/cart", response_class=HTMLResponse)
async def read_cart_page(request: Request, current_user: User = Depends(get_current_active_user)):
    """Example of a cart page that needs admin check."""
    
    # Check if the user is admin and redirect if needed
    redirect_response = await redirect_admin_to_admin_page(request, current_user)
    if redirect_response:
        return redirect_response

    return templates.TemplateResponse("cart.html", {"request": request, "user": current_user})

# Example of another endpoint that would require the same check
@app.get("/form", response_class=HTMLResponse)
async def read_form_page(request: Request, current_user: User = Depends(get_current_active_user)):
    """Example of a form page that needs admin check."""
    
    # Check if the user is admin and redirect if needed
    redirect_response = await redirect_admin_to_admin_page(request, current_user)
    if redirect_response:
        return redirect_response

    return templates.TemplateResponse("form.html", {"request": request, "user": current_user})
