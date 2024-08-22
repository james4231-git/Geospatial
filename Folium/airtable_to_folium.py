import folium
# from geopy.geocoders import Nominatim
import webbrowser
import os
import time

import json
from pyairtable import Api

with open('../my_credentials.json') as f:
    credentials = json.loads(f.read())

baseId = credentials['base']
key = credentials["key"]

# base = Airtable(baseId, key)
# places = base.get('Vancouver and Banff')
api = Api(key)
base = api.base(baseId)
table = base.table('Vancouver & Banff')
records = table.all()

icon_map = {
    "Lodging": ['bed'],
    "Activity": ['person-walking'],
    "Attraction": ['landmark'],
    "Dinner": ['plate-wheat'],
    "Lunch": ['burger'],
    "Breakfast/Coffee": ['mug-hot'],
    "Dining": ['utensils'],
    "Drinks": ['martini-glass'],
    "Bars": ['martini-glass'],
    "Winery": ['wine-bottle'],
    "Brewery": ['beer-mug'],
}

# geolocator = Nominatim(user_agent="airtable_to_folium")

# Step 2: Create a map centered at the location
map_ = folium.Map(location=[50.65453570942645, -120.30424611826452], zoom_start=7)

base = folium.FeatureGroup(name='Base')
dining = folium.FeatureGroup(name='Dining')
drinks = folium.FeatureGroup(name='Drinks')
activities = folium.FeatureGroup(name='Activities')

for record in records:

    fields = record['fields']

    # Step 1: Geocode the address to get latitude and longitude
    # location = geolocator.geocode(fields['Address'])
    name = fields['Item']
    location_type = fields['Type']  # Example type
    if type in ['Costs', 'Travel']:
        # don't map these types
        # print("Skipping %s of type %s" % (fields['Item'], type))
        continue

    try:
        # latitude, longitude = location.latitude, location.longitude
        coordinates = fields['Coordinates']
        # Split the string into latitude and longitude
        latitude, longitude = map(float, coordinates.split(','))
    except KeyError:
        print("Couldn't find %s" % (name))
        continue

    try:
        href = fields['URL']
    except KeyError:
        href = fields['Google Search']

    # Step 3: Define the location type and corresponding icon
    popup = '<a href="%s">%s</a>' % (href, name)

    # Step 4: Add a marker with a custom icon and a link
    try:
        icon = icon_map[location_type]
    except KeyError:
        icon = ['location-dot']
    group = base
    icon_color = 'gray'
    if location_type in ['Activity', 'Attraction']:
        group = activities
        icon_color = 'blue'
    if location_type in ['Dinner', 'Lunch', 'Breakfast/Coffee', 'Dining']:
        group = dining
        icon_color = 'red'
    if location_type in ['Bars', 'Winery', 'Brewery']:
        group = drinks
        icon_color = 'purple'
    group.add_child(
        folium.Marker(
            [latitude, longitude],
            popup=popup,  # Example URL
            icon=folium.Icon(icon=icon[0], prefix='fa', color=icon_color),
            tooltip=name
        ))

map_.add_child(base)
map_.add_child(activities)
map_.add_child(dining)
map_.add_child(drinks)

# Step 5: Add layer control to toggle the feature groups
folium.LayerControl().add_to(map_)

# Step 5: Save the map as an HTML file
file_path = "../output/folium_map.html"
map_.save(file_path)

# Step 6: Open the map in the default web browser on Mac
webbrowser.open('file://' + os.path.realpath(file_path))