from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from pymongo import MongoClient
import json
from bson import ObjectId
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

# Custom JSON Encoder to handle ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

# Initialize Flask app
app = Flask(__name__, static_url_path='/static')
app.json_encoder = JSONEncoder  # Use the custom JSON encoder
app.secret_key = 'your_secret_key'  # Add a secret key for session management

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['HoustonTaxiDB']

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login_user'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def landing_page():
    return render_template('landing_page.html')

@app.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        data = {
            "username": request.form['username'],
            "password": generate_password_hash(request.form['password'])
        }
        db.users.insert_one(data)
        return jsonify({"message": "User registered successfully!"}), 201
    return render_template('register_user.html')

@app.route('/login_user', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.users.find_one({"username": username})
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('user_dashboard'))
        else:
            return jsonify({"message": "Invalid username or password!"}), 401
    return render_template('login_user.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login_user'))

@app.route('/register_driver', methods=['GET', 'POST'])
def register_driver():
    if request.method == 'POST':
        data = {
            "username": request.form['username'],
            "password": generate_password_hash(request.form['password']),
            "taxi_id": request.form['taxi_id'],
            "driver_name": request.form['driver_name'],
            "location": {
                "type": "Point",
                "coordinates": [float(request.form['longitude']), float(request.form['latitude'])]
            }
        }
        db.drivers.insert_one(data)
        return jsonify({"message": "Driver registered successfully!"}), 201
    return render_template('register_driver.html')

@app.route('/login_driver', methods=['GET', 'POST'])
def login_driver():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        driver = db.drivers.find_one({"username": username})
        if driver and check_password_hash(driver['password'], password):
            session['username'] = username
            return redirect(url_for('driver_dashboard'))
        else:
            return jsonify({"message": "Invalid username or password!"}), 401
    return render_template('login_driver.html')

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    return render_template('user_dashboard.html')

@app.route('/driver_dashboard')
@login_required
def driver_dashboard():
    return render_template('driver_dashboard.html')

@app.route('/register_taxi', methods=['GET', 'POST'])
@login_required
def register_taxi():
    if request.method == 'POST':
        data = {
            "taxi_id": request.form['taxi_id'],
            "driver_name": request.form['driver_name'],
            "location": {
                "type": "Point",
                "coordinates": [float(request.form['longitude']), float(request.form['latitude'])]
            }
        }
        db.taxis.insert_one(data)
        return jsonify({"message": "Taxi registered successfully!"}), 201
    return render_template('register_taxi.html')

@app.route('/update_taxi_location', methods=['POST'])
@login_required
def update_taxi_location():
    data = request.json
    db.taxis.update_one(
        {"taxi_id": data["taxi_id"]},
        {"$set": {"location": data["location"]}}
    )
    return jsonify({"message": "Taxi location updated successfully!"}), 200

@app.route('/request_taxi', methods=['POST'])
@login_required
def request_taxi():
    data = request.json
    user_location = data['location']
    taxi_preference = data['taxi_preference']
    
    query = {
        "location": {
            "$near": {
                "$geometry": user_location,
                "$maxDistance": 5000  # within 5 km radius
            }
        }
    }
    
    if taxi_preference != 'Any':
        query["type"] = taxi_preference
    
    available_taxis = list(db.taxis.find(query).limit(5))
    
    # Convert MongoDB documents to JSON-serializable format
    for taxi in available_taxis:
        taxi['_id'] = str(taxi['_id'])
    
    return jsonify(available_taxis), 200

if __name__ == '__main__':
    app.run(debug=True)
