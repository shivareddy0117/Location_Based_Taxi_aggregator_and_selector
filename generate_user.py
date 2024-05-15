import random
import json
import time

def generate_random_users(num_users, bounds):
    southwest_lat = bounds['southwest']['lat']
    southwest_lng = bounds['southwest']['lng']
    northeast_lat = bounds['northeast']['lat']
    northeast_lng = bounds['northeast']['lng']

    users = []
    for i in range(1, num_users + 1):
        # Generate random location within bounds
        lat = random.uniform(southwest_lat, northeast_lat)
        lng = random.uniform(southwest_lng, northeast_lng)

        # Randomly assign a taxi type preference to the user
        taxi_preference = random.choice(['Luxury', 'Deluxe', 'Standard', 'Any'])

        # Create the user dictionary
        user = {
            "user_id": f"User{str(i).zfill(3)}",
            "location": {
                "type": "Point",
                "coordinates": [lng, lat]  # Note: longitude first, then latitude
            },
            "taxi_preference": taxi_preference
        }
        users.append(user)

    return users

def simulate_user_requests(users):
    while True:
        # Select a random user to make a request
        user = random.choice(users)
        print(f"User {user['user_id']} at {user['location']['coordinates']} requests a {user['taxi_preference']} taxi.")
        time.sleep(60)  # Wait for 60 seconds before the next request

# Define the geographic bounds of Downtown Houston
bounds = {
    "southwest": {"lat": 29.677188413138673, "lng": -95.47487010411909},
    "northeast": {"lat": 29.82116771080327, "lng": -95.25459367187106}
}

# Generate data for 5 users
random_users = generate_random_users(5, bounds)

# Start simulating user taxi requests
simulate_user_requests(random_users)
