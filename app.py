from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import json
from bson import ObjectId

# Custom JSON Encoder to handle ObjectId
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

# Initialize Flask app
app = Flask(__name__)
app.json_encoder = JSONEncoder  # Use the custom JSON encoder

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['HoustonTaxiDB']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register_taxi', methods=['POST'])
def register_taxi():
    data = request.json
    db.taxis.insert_one(data)
    return jsonify({"message": "Taxi registered successfully!"}), 201

@app.route('/register_user', methods=['POST'])
def register_user():
    data = request.json
    db.users.insert_one(data)
    return jsonify({"message": "User registered successfully!"}), 201

@app.route('/update_taxi_location', methods=['POST'])
def update_taxi_location():
    data = request.json
    db.taxis.update_one(
        {"taxi_id": data["taxi_id"]},
        {"$set": {"location": data["location"]}}
    )
    return jsonify({"message": "Taxi location updated successfully!"}), 200

@app.route('/request_taxi', methods=['POST'])
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
