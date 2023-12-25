from flask import Flask, render_template, request, redirect, url_for, session, send_file, abort
from flask_sqlalchemy import SQLAlchemy
import os
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# SQLAlchemy Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/db_name'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Replace with your email server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'  # Replace with your email credentials
app.config['MAIL_PASSWORD'] = 'your_email_password'
db = SQLAlchemy(app)
mail = Mail(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    verified = db.Column(db.Boolean, default=False)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    filepath = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('files', lazy=True))

@app.route('/')
def index():
    return render_template('index.html', variable='value')

#  user data (Replace this with user registration logic)
users = {
    'user1': {'email': 'user1@example.com', 'password': 'password1', 'role': 'Ops'},
    'user2': {'email': 'user2@example.com', 'password': 'password2', 'role': 'Client'}
}

# function for verifying credentials
@app.route('/')
def verify_user(username, password):
    return users.get(username) if users.get(username) and users[username]['password'] == password else None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = verify_user(username, password)
        if user:
            # Set up a session upon successful login
            session['user_id'] = user.id
            return redirect(url_for('dashboard')) 
        else:
            error = 'Invalid credentials. Please try again.'
            return render_template('login.html', error=error)
    
    return render_template('login.html')  # Render the login form

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('upload.html', message='No file part')

        file = request.files['file']

        if file.filename == '':
            return render_template('upload.html', message='No selected file')

        if file:
            # Save the file to the configured upload folder
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            return render_template('upload.html', message='File uploaded successfully')

    return render_template('upload.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Check if all required fields are present in the form data
        if 'username' in request.form and 'email' in request.form and 'password' in request.form:
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']

            # Check if the username or email already exists in the database
            existing_user = User.query.filter_by(username=username).first()
            existing_email = User.query.filter_by(email=email).first()

            if existing_user or existing_email:
                return render_template('signup.html', message='Username or email already exists!')

            # Create a new user and add to the database
            new_user = User(username=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()

            # Redirect to login page after successful signup
            return redirect(url_for('login'))
        else:
            return render_template('signup.html', message='Please fill in all the required fields.')

    return render_template('signup.html')

@app.route('/verify_email/<token>', methods=['GET'])
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()

    if user:
        user.verified = True
        user.verification_token = None  # Clear the verification token after successful verification
        db.session.commit()
        return render_template('email_verified.html')
    else:
        abort(404)  # Handle the case when the token is invalid or user not found


def send_verification_email(email, token):
    msg = Message('Email Verification', sender='your_email@gmail.com', recipients=[email])
    msg.body = f"Click the following link to verify your email: http://localhost:5000/verify_email/{token}"
    mail.send(msg)
    mail=Mail(app)

file_paths = {
    'file1': '/path/to/file1.pdf',
    'file2': '/path/to/file2.docx',
    # Add more file paths as needed
}

def get_file_path_from_database(file_id):
    # Assuming using SQLAlchemy and have a File model
    file_record = File.query.filter_by(id=file_id).first()
    
    if file_record:
        return file_record.file_path  # Adjust this according to database schema
    else:
        return None

@app.route('/download/<file_id>', methods=['GET'])
def download(file_id):
    file_path = get_file_path_from_database(file_id)

    if file_path:
        if os.path.exists(file_path):  # Check if file exists at the provided path
            return send_file(file_path, as_attachment=True)
        else:
            return 'File not found on the server', 404
    else:
        return 'File information not found', 404


# Dictionary to hold uploaded files (replace this with file storage logic)
uploaded_files = {
    1: {'name': 'File1.pdf', 'path': '/path/to/File1.pdf'},
    2: {'name': 'File2.docx', 'path': '/path/to/File2.docx'},
    # Add more files as needed
}

@app.route('/list_files', methods=['GET'])
def list_files():
    # Get all file details for listing
    files_list = [{'id': file_id, 'name': file_data['name']} for file_id, file_data in uploaded_files.items()]

    return render_template('list_files.html', files=files_list)

if __name__ == '__main__':
    app.run(debug=True)
