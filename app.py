import os
import requests
from flask import Flask, render_template, request, redirect, url_for, flash,jsonify
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
    city_id = db.Column(db.Integer, db.ForeignKey('city.id'), nullable=False)

class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    detail=db.Column(db.String(400), nullable=True)
    longitude = db.Column(db.Float, nullable=False)
    visited = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
# Load user function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def get_coordinates(city_name):
    api_key = 'f4ae94146a744187b2f78b6637aaec82'  # Replace with your OpenCage API key
    url = f'https://api.opencagedata.com/geocode/v1/json?q={city_name}&key={api_key}'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            latitude = data['results'][0]['geometry']['lat']
            longitude = data['results'][0]['geometry']['lng']
            return latitude, longitude
        else:
            return None, None  # No results found for the city
    else:
        return None, None  # API request failed

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
        print(username,email)
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
    cities=City.query.filter_by(user_id=current_user.id).all()
    visited_countries = len(set(city.name.split(",")[-1] for city in cities if city.visited))
    total_countries = 195
    return render_template('home.html',cities=cities, visited_count=visited_countries, total_count=total_countries,current_user=current_user)

@app.route('/<int:city_id>', methods=['GET', 'POST'])
@login_required
def city(city_id):
    if request.method == 'POST':
        files = request.files.getlist('file') 
        for file in files:
            if file and allowed_file(file.filename):
                # Generate a secure filename
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Save the file to the server inside 'static/uploads'
                file.save(file_path)
                
                # Save the file info to the database
                new_upload = Upload(user_id=current_user.id,city_id=city_id, file_path=f'uploads/{filename}')
                print(f'uploads/{filename}')
                db.session.add(new_upload)
                db.session.commit()
                city = City.query.get(city_id)
                uploads = Upload.query.filter_by(user_id=current_user.id,city_id=city.id).all()
            else:
                flash('Invalid file type!', 'danger')
        return redirect(url_for('city', city_id=city_id, uploads=uploads,current_user=current_user))
    
    city = City.query.get(city_id)
    uploads = Upload.query.filter_by(user_id=current_user.id,city_id=city.id).all()
    if city.user_id==current_user.id:
        return render_template("city.html",city=city, uploads=uploads,current_user=current_user)
    else:
        return "Access Denied"
    
@app.route('/<int:city_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_rec(city_id):
    record = City.query.get(city_id)

    if record:
        db.session.delete(record)
        db.session.commit()
        return redirect(url_for('home'))
    else:
        print("Record not found")

@app.route('/api/cities', methods=['GET'])
def get_cities():
    cities = City.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': city.id,
        'name': city.name,
        'latitude': city.latitude,
        'longitude': city.longitude,
        'visited': city.visited
    } for city in cities])

@app.route('/add', methods=['POST'])
def add_city():
    city_name = request.form['city']
    famous_places = request.form['famous_places']
    
    latitude, longitude = get_coordinates(city_name)
    
    if latitude is not None and longitude is not None:
        new_city = City(name=city_name, latitude=latitude, longitude=longitude,detail=famous_places, visited=False,user_id=current_user.id)
        db.session.add(new_city)
        db.session.commit()
        return redirect(url_for('home'))
    else:
        return "Error: Could not find coordinates for the city."

@app.route('/visit/<int:city_id>', methods=['POST'])
def visit_city(city_id):
    city = City.query.get(city_id)
    city.visited = not city.visited
    db.session.commit()
    return "City marked as visited!"
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
    
