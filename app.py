from flask import Flask, request, jsonify, render_template, session
from pymongo import MongoClient
import json
from bson import ObjectId
from flask_cors import CORS, cross_origin
import requests
from flask_socketio import SocketIO, send, emit


app = Flask(__name__)
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")
app.secret_key = '12345abcd'


# Custom JSON Encoder to handle ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


# Initialize Flask app
app.json_encoder = JSONEncoder  # Use the custom JSON encoder

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['HoustonTaxiDB']
subscriptions_collection = db['subscriptions']


@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')
@socketio.on('/notification')
@cross_origin(origins=['http://localhost:3000'])
def notification(message):
    print("inside")
    # Handle notification logic here
    if message == 'Welcome to taxi rides!':
        # Send the notification to the client
        emit('notification_response', 'Welcome to taxi rides!')

@app.route('/login', methods=['POST'])
@cross_origin(origins=['http://localhost:3000'], methods=['POST'], headers=['Content-Type'])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    session_id = data.get('sessionID')

    # Check if the email and password match in the login_details collection
    user = db.login_details.find_one({"email": email, "password": password})

    if user:
        session['user_id'] = str(user['_id'])
        # Update the login_details collection with the session_id
        db.login_details.update_one(
            {"_id": user['_id']},
            {"$set": {"session_id": session_id}}
        )
        # If user exists, return true along with the session ID
        return jsonify({"authenticated": True, "session_id": session_id}), 200
    else:
        # If user doesn't exist, return false
        return jsonify({"authenticated": False}), 401



@app.route('/register_taxi', methods=['POST'])
@cross_origin(origins=['http://localhost:3000'], methods=['POST'], headers=['Content-Type'])
def register_taxi():
    data = request.json
    db.taxis.insert_one(data)

    return jsonify({"message": "Taxi registered successfully!"}), 201


@app.route('/register_user', methods=['POST'])
@cross_origin(origins=['http://localhost:3000'], methods=['POST'], headers=['Content-Type'])
def register_user():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")
    db.users.insert_one(data)
    db.login_details.insert_one({"email": email, "password": password, "role": role})
    return jsonify({"message": "User registered successfully!"}), 201


@app.route('/update_taxi_location', methods=['POST'])
@cross_origin(origins=['http://localhost:3000'], methods=['POST'], headers=['Content-Type'])
def update_taxi_location():
    data = request.json
    db.taxis.update_one(
        {"taxi_id": data["taxi_id"]},
        {"$set": {"location": data["location"]}}
    )
    return jsonify({"message": "Taxi location updated successfully!"}), 200


@app.route('/request_taxi', methods=['POST'])
@cross_origin(origins=['http://localhost:3000'], methods=['POST'], headers=['Content-Type'])
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


@app.route('/subscribe', methods=['POST'])
@cross_origin(origins=['http://localhost:63342'], methods=['POST'], headers=['Content-Type'])
def subscribe():
    try:
        # Get subscription data from request body
        subscription_data = request.json

        # Store subscription data in MongoDB
        result = subscriptions_collection.insert_one(subscription_data)

        if result.inserted_id:
            return jsonify({"success": True, "message": "Subscription stored successfully"}), 200
        else:
            return jsonify({"success": False, "message": "Failed to store subscription"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": "An error occurred", "error": str(e)}), 500

@app.route('/send_notification', methods=['POST'])
@cross_origin(origins=['http://localhost:3000'], methods=['POST'], headers=['Content-Type'])
def send_notification_route():
    try:
        # Trigger notification logic (e.g., new event, message, update)
        notification_data = {
            'title': 'New Notification',
            'body': 'This is a push notification from your Flask app!',
            'icon': '/icon.png',
            'badge': '/badge.png'
        }

        # Retrieve subscription data from MongoDB
        subscriptions = subscriptions_collection.find({})

        # Send notifications to subscribed clients
        for subscription in subscriptions:
            send_notification(subscription['endpoint'], json.dumps(notification_data), ttl=10000)

        return jsonify({"success": True, "message": "Notifications sent successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": "An error occurred", "error": str(e)}), 500

def send_notification(endpoint, data, ttl):
    headers = {
        'Authorization': 'key=H1kGphJ48unczqeLJJsiJiNuL75p5xGihsCJCGBR1yI',
        'Content-Type': 'application/json'
    }

    response = requests.post(endpoint, headers=headers, data=data)
    if response.status_code == 200:
        print("Notification sent successfully to:", endpoint)
    else:
        print("Failed to send notification to:", endpoint)

@socketio.on("test", namespace='/login')
def handle_login(data):
    email = data.get("email")
    password = data.get("password")
    session_id = request.sid

    print("sessionid", session_id)
    # Check if the email and password match in the login_details collection
    user = db.login_details.find_one({"email": email, "password": password})

    if user:
        # If user exists, emit a login success event
        socketio.emit('login_response', {"authenticated": True}, room=session_id)
    else:
        # If user doesn't exist, emit a login failure event
        socketio.emit('login_response', {"authenticated": False}, room=session_id)

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=5000, allow_unsafe_werkzeug=True)
