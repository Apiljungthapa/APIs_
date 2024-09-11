# FastAPI and Flask Authentication Systems

This repository contains two separate folders, each implementing an API authentication system using different Python frameworks:

1. **Flask App**: A login and registration system that includes live YOLO detection after successful login, with database connectivity.
2. **FastAPI JWT Authentication**: An API with JWT-based authentication, login system, admin user page, cart page, and user-admin privileges management.


### Common Setup Instructions

**Clone the Repository**:

   ```bash
   git clone https://github.com/Apiljungthapa/Fastapi_JWT_AUTHENTICATION.git
   ```

## 1. Flask App: Login and Registration with YOLO Detection

### Overview

The Flask app provides a login and registration system. After a successful login, the app detects live objects using YOLO (You Only Look Once) with a database connection.

### Features

- User Registration
- User Login
- Live YOLO Object Detection after successful login
- Database connectivity for user data management

1.1 Navigating to folder path:
   ```bash
   cd flask_app
   ```

1.2 Install Dependencies:
 ```bash
  pip install -r requirements.txt
 ```
1.3 Configure Database:

    Set up the database by creating necessary tables. You may use a tool like SQLite or any other database supported by Flask.

1.4 Run the Application:
   ```bash
   python app.py
   ```
1. 5 Access the Application:

    The app will be running at `http://localhost:5000`.

#### Usage:

Register a new user account.

Log in using the registered credentials.

After logging in, access the YOLO detection page to start live object detection.

### 2. FastAPI JWT Authentication System
Overview
The FastAPI project provides a complete JWT authentication system, including a login system, admin user page, cart page, and user-admin privileges management.

Features
JWT-based User Authentication
User Login and Registration
Admin User Management Page
Cart Management Page
User and Admin Privileges

2.1 Navigating to folder path:
   ```bash
   cd Fastapi_JWT AUTHENTICATION
   ```

2.2 Install Dependencies:
 ```bash
  pip install -r requirements.txt
 ```

2.3 Run the Application:
   ```bash
   uvicorn main:app --reload

   ```
2.4 Access the Application:

    The app will be running at `http://localhost:8000`


