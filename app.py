import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Update the path to point to the 'uploads' folder inside the 'static' directory
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # or your preferred database URI
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')  # Points to WanderMap/static/uploads
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    uploads = db.relationship('Upload', backref='user', lazy=True)

# Upload model
class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(150), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Load user function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route for the landing page (index.html)
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('home'))  # Redirect to home if user is logged in
    return render_template('index.html')

# Route for login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Login failed. Check your email and/or password.', 'danger')
    
    return render_template('login.html')

# Route for register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    
    return render_template('register.html')

# Route for home page (where user can upload pictures)
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            # Generate a secure filename
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the file to the server inside 'static/uploads'
            file.save(file_path)
            
            # Save the file info to the database
            new_upload = Upload(user_id=current_user.id, file_path=f'uploads/{filename}')
            print(f'uploads/{filename}')
            db.session.add(new_upload)
            db.session.commit()
            
            flash('File uploaded successfully!', 'success')
        else:
            flash('Invalid file type!', 'danger')

    # Fetch uploads for the current user
    uploads = Upload.query.filter_by(user_id=current_user.id).all()
    return render_template('home.html', uploads=uploads)

# Route to handle logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# Helper function to check file extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Initialize the database (run this once to create the tables)
@app.before_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
