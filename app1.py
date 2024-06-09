from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
from pymongo import MongoClient
import threading
import time
from datetime import datetime
import requests

app = Flask(__name__, static_url_path='/static')
CORS(app)
socketio = SocketIO(app)

# Update this line with your MongoDB Atlas connection string
client = MongoClient('mongodb+srv://CloudProjectGroup01:dbhEGgjTGz2WjSGk@cluster0.ejz2u2z.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['HoustonTaxiDB']
taxis_collection = db['taxis']
rides_collection = db['rides']

if taxis_collection.count_documents({}) == 0:
    initial_data = {
        'taxi_id': 'Taxi001',
        'type': 'Luxury',
        'location': {
            'type': 'Point',
            'coordinates': [-95.3698, 29.7604]
        }
    }
    taxis_collection.insert_one(initial_data)
    print("Initial taxi data inserted.")

def get_route(start, end):
    url = f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}?overview=full&geometries=geojson"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        route = data['routes'][0]['geometry']['coordinates']
        return [(lat, lon) for lon, lat in route]
    else:
        print("Error fetching route from OSM")
        return []

def move_taxi(taxi_id, route, ride_id):
    covered_path = []
    for current_position in route:
        timestamp = datetime.utcnow()
        taxis_collection.update_one(
            {'taxi_id': taxi_id},
            {'$set': {'location': {'type': 'Point', 'coordinates': [current_position[1], current_position[0]]}}}
        )
        rides_collection.update_one(
            {'ride_id': ride_id},
            {'$push': {'path': {'location': current_position, 'timestamp': timestamp}}}
        )
        covered_path.append(current_position)
        socketio.emit('taxi_update', {
            'lat': current_position[0],
            'lng': current_position[1],
            'taxi_id': taxi_id,
            'covered_path': covered_path,
            'full_route': route
        })
        time.sleep(1)

@app.route('/')
def index():
    return render_template('map.html')

@app.route('/show_map', methods=['GET'])
def show_map():
    print("show_map endpoint hit")  # Debug print
    start_lat = float(request.args.get('start_lat'))
    start_lng = float(request.args.get('start_lng'))
    end_lat = float(request.args.get('end_lat'))
    end_lng = float(request.args.get('end_lng'))

    print(f"Start location: {start_lat}, {start_lng}")  # Debug print
    print(f"End location: {end_lat}, {end_lng}")  # Debug print

    ride_id = 'Ride001'
    user_id = 'User001'
    taxi_id = 'Taxi001'
    start_location = [start_lat, start_lng]
    end_location = [end_lat, end_lng]
    start_time = datetime.utcnow()

    ride_data = {
        'ride_id': ride_id,
        'user_id': user_id,
        'taxi_id': taxi_id,
        'start_location': start_location,
        'end_location': end_location,
        'start_time': start_time,
        'path': []
    }
    rides_collection.insert_one(ride_data)
    print(f"Started ride {ride_id} from {start_location} to {end_location}")  # Debug print

    # Fetch route and start taxi movement simulation in a new thread
    route = get_route(start_location, end_location)
    if route:
        # Emit the full route once
        socketio.emit('route_init', {'full_route': route})
        taxi_thread = threading.Thread(target=move_taxi, args=(taxi_id, route, ride_id))
        taxi_thread.start()

    return render_template('map.html')

@socketio.on('connect')
def test_connect():
    print('Client connected')

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    print("Starting Flask app...")
    socketio.run(app, debug=True)
