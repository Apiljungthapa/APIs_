from flask import Flask,render_template,request,redirect,url_for,flash,session,Response,send_from_directory
import logging
import mysql.connector as conn
# from werkzeug.security import generate_password_hash
import re
import cv2
import torch
from ultralytics import YOLO
from io import BytesIO
import os
import numpy as np
from werkzeug.utils import secure_filename



app = Flask(__name__)
app.config['SECRET_KEY'] = 'apil123'

app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['DETECTED_FOLDER'] = 'static/detected/'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DETECTED_FOLDER'], exist_ok=True)

@app.route('/')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/home')
def home_page():
    
     return render_template('home.html')  

    # else:
    #     flash('You need to log in first.', 'error')
    #     return redirect(url_for('login'))





@app.route("/login_validate", methods=['POST'])

def login_validate():

    email= request.form.get("email")
    password = request.form.get("password")

    try:
        # Establish the connection
        connection = conn.connect(
            host='localhost',
            user='root',
            password='',  # Use the appropriate password if set
            database='users'  # Replace with your database name
        )

        if connection.is_connected():
            cursor = connection.cursor()
            
            # Query to check user credentials
            query = "SELECT * FROM user WHERE email = %s AND password = %s"
            cursor.execute(query, (email, password))
            user = cursor.fetchone()

            if user:
                # session['user_id'] = user[0]  # Store user ID in session
                flash('You have successfully logged in!', 'success')
                return redirect(url_for('home_page'))
            
            else:
                # Flash error message before redirecting to the login page
                flash('Incorrect email or password', 'error_msg')
                return render_template('login.html', email=email)  # Make sure the route name is correct


    except conn.Error as e:
        logging.error(f"Error while connecting to MySQL: {e}")
        flash('Database connection failed. Please try again later.', 'error')
        return render_template('login.html', email=email)

    finally:
        # Ensure connection is closed if it was successfully created
        if connection is not None and connection.is_connected():
            connection.close()

@app.route("/add_register", methods=['POST'])
def add_register():
    # Get form data
    username = request.form.get("username")
    email = request.form.get("email")
    number = request.form.get("number")
    fullname = request.form.get("full")
    password = request.form.get("password")
    confirmpassword = request.form.get("confirm_password")

    # Validate the form data
    if not username or not fullname or not number or not password or not confirmpassword:
        flash('All fields are required. Please fill out the form completely.', 'error')
        return render_template('register.html', username=username, email=email, number=number, fullname=fullname, password=password)

    if "@" not in email:
        flash('Invalid email format.', 'error')
        return render_template('register.html', username=username, email=email, number=number, fullname=fullname,password=password)

    if password != confirmpassword:
        flash('Passwords do not match.', 'error')
        return render_template('register.html', username=username, email=email, number=number, fullname=fullname,password=password)



    connection = None
    cursor = None

    try:
        # Establish the connection
        connection = conn.connect(
            host='localhost',
            user='root',
            password='',  # Use the appropriate password if set
            database='users'  # Replace with your database name
        )

        # Hash the password
        # hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        if connection.is_connected():
            cursor = connection.cursor()
            
            # Query to insert user data
            query = "INSERT INTO user (username, email, full_name, contact, password) VALUES (%s, %s, %s, %s, %s)"
            values = (username, email, number, fullname, password)
            
            # Execute the query
            cursor.execute(query, values)
            
            # Commit the transaction
            connection.commit()
            
            # Redirect to a success page or another route
            flash(f'Account created for {username}!', 'reg_success')
            return redirect(url_for('login'))
    
    except conn.Error as e:
        logging.error(f"Error while connecting to MySQL: {e}")
        return "An error occurred. Please try again later."

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.route('/Register_success')
def reg_success():
    return "Registration successful!"


@app.route('/Login_success')
def log_success():
    return "Login successful!"


# @app.route("/login")
# def login():
#     return render_template('login.html')


# Load the YOLOv8 model
model = YOLO('yolov8n.pt')  # Replace with your specific YOLOv8 weights

def generate_frames():
    # Initialize the webcam
    cap = cv2.VideoCapture(0)  # '0' is the default camera

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Perform YOLOv8 detection
        results = model(frame)

        # Process results and draw bounding boxes
        for result in results:
            for box in result.boxes:
                # Extract bounding box and confidence score
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
                conf = box.conf[0]  # Confidence score
                cls = int(box.cls[0])  # Class id
                label = model.names[cls]  # Get label from class id
                
                # Draw bounding box and label on the frame
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f'{label} {conf:.2f}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        # Encode the frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Yield the frame to the browser
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')



if __name__ == "__main__":

    app.run(debug=True)


