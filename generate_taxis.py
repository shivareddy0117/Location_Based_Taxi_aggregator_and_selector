import random
import json

def generate_random_taxis(num_taxis, bounds):
    southwest_lat = bounds['southwest']['lat']
    southwest_lng = bounds['southwest']['lng']
    northeast_lat = bounds['northeast']['lat']
    northeast_lng = bounds['northeast']['lng']
    
    taxis = []
    for i in range(1, num_taxis + 1):
        # Generate random location within bounds
        lat = random.uniform(southwest_lat, northeast_lat)
        lng = random.uniform(southwest_lng, northeast_lng)
        
        # Randomly assign a type to the taxi
        taxi_type = random.choice(['Luxury', 'Deluxe', 'Standard'])
        
        # Create the taxi dictionary
        taxi = {
            "name": f"Taxi{str(i).zfill(3)}",
            "type": taxi_type,
            "location": {
                "type": "Point",
                "coordinates": [lng, lat]  # Note: longitude first, then latitude
            }
        }
        taxis.append(taxi)
    
    return taxis

# Define the geographic bounds of Downtown Houston
bounds = {
    "southwest": {"lat": 29.677188413138673, "lng": -95.47487010411909},
    "northeast": {"lat": 29.82116771080327, "lng": -95.25459367187106}
}

# Generate data for 50 taxis
random_taxis = generate_random_taxis(50, bounds)

# Print the JSON output
print(json.dumps(random_taxis, indent=2))
