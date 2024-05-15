import folium
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['HoustonTaxiDB']
taxis_collection = db['taxis']

# Fetch taxi data
taxis = list(taxis_collection.find())

# Initialize a map centered around Downtown Houston
m = folium.Map(location=[29.7604, -95.3698], zoom_start=13)

# Add taxi locations to the map
for taxi in taxis:
    folium.Marker(
        location=[taxi['location']['coordinates'][1], taxi['location']['coordinates'][0]],  # Lat, Lon
        popup=f"Taxi ID: {taxi['taxi_id']}\nType: {taxi['type']}"
    ).add_to(m)

# Save the map to an HTML file
m.save('taxi_locations.html')

print("Map has been created and saved as taxi_locations.html")
