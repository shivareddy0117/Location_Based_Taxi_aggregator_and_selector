import folium
from pymongo import MongoClient
from folium import features

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['HoustonTaxiDB']
taxis_collection = db['taxis']

# Fetch taxi data
taxis = list(taxis_collection.find())

# Initialize a map centered around Downtown Houston
m = folium.Map(location=[29.7604, -95.3698], zoom_start=13)

# Define icon paths
icons = {
    'Utility': r'C:\Users\SAHITHYAMOGILI\Desktop\Projects\Location_Based_Taxi_aggregator_and_selector\static\utility.png',
    'Deluxe': r'C:\Users\SAHITHYAMOGILI\Desktop\Projects\Location_Based_Taxi_aggregator_and_selector\static\deluxe.png',
    'Luxury': r'C:\Users\SAHITHYAMOGILI\Desktop\Projects\Location_Based_Taxi_aggregator_and_selector\static\luxury.png'
}

# Loop through each taxi and place it on the map
for taxi in taxis:
    # Get the appropriate icon for each taxi type
    icon_url = icons.get(taxi['type'], r"C:\Users\SAHITHYAMOGILI\Desktop\Projects\Location_Based_Taxi_aggregator_and_selector\static\default.png")  # Default icon if type not matched
    icon = folium.CustomIcon(
        icon_image=icon_url,
        icon_size=(30, 30),  # Size of the icon in pixels
        icon_anchor=(15, 15)  # Anchor point of the icon (half of size to center)
    )
    
    folium.Marker(
        location=[taxi['location']['coordinates'][1], taxi['location']['coordinates'][0]],  # Lat, Lon
        icon=icon,
        popup=f"Taxi ID: {taxi['taxi_id']}\nType: {taxi['type']}"
    ).add_to(m)

# Save the map to an HTML file
m.save('taxi_locations.html')

print("Map has been created and saved as taxi_locations.html")
