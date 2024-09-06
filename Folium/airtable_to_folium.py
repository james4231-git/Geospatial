import folium
import webbrowser
import os

from airtable_class import Table, get_parser

base_name= 'Travel'  # "James' Cheat Sheet"
table_name = 'Vancouver & Banff'
field_name = 'Item'

parser = get_parser()
args = parser.parse_args()

if args.Base and args.Table:
    base_name = args.Base
    table_name = args.Table
    field_name = args.Field

table = Table(base_name,table_name)

icon_map = {
    "Lodging": ['bed'],
    "Place To Stay": ['bed'],
    "Activity": ['person-walking'],
    "Things To Do": ['person-walking'],
    "Biking": ['person-walking'],
    "Hiking": ['person-walking'],
    "Attraction": ['landmark'],
    "Dinner": ['plate-wheat'],
    "Lunch": ['burger'],
    "Breakfast/Coffee": ['mug-hot'],
    "Coffee/Bakery": ['mug-hot'],
    "Dessert": ['ice-cream'],
    "Dining": ['utensils'],
    "Restaurant": ['utensils'],
    "GF Restaurant": ['wheat-awn-circle-exclamation'],
    "Drinks": ['martini-glass'],
    "Bars": ['martini-glass'],
    "Bar": ['martini-glass'],
    "Distillery": ['martini-glass'],
    "Winery": ['wine-bottle'],
    "Brewery": ['beer-mug'],
    "GF Brewery": ['beer-mug'],
    "Travel": ['van-shuttle'],
    "Generic": ['location-dot']
}

# Step 2: Create a map centered at the location
map_ = folium.Map(location=[50.65453570942645, -120.30424611826452], zoom_start=7)

base = folium.FeatureGroup(name='Base')
dining = folium.FeatureGroup(name='Dining')
drinks = folium.FeatureGroup(name='Drinks')
activities = folium.FeatureGroup(name='Activities')
travel = folium.FeatureGroup(name='Travel')

for record in table.records:

    fields = record.fields

    # Step 1: Geocode the address to get latitude and longitude
    # location = geolocator.geocode(fields['Address'])
    name = fields[field_name]
    location_type = fields['Type'] # Example type

    # Step 4: Add a marker with a custom icon and a link
    try:
        icon = icon_map[location_type]
    except KeyError:
        print('Not plotting %s %s' % (location_type, name))
        continue

    try:
        # latitude, longitude = location.latitude, location.longitude
        coordinates = fields['Coordinates']
        # Split the string into latitude and longitude
        latitude, longitude = map(float, coordinates.split(','))
    except KeyError:
        print("No coordinates for %s" % (name))
        continue

    try:
        site_url = fields['URL']
    except KeyError:
        site_url = fields['Google Search']

    try:
        map_url = fields['Map URL']
    except KeyError:
        map_url = fields['Google Maps Query']

    record_url  = fields['Record URL']

    # Step 3: Define the location type and corresponding icon
    popup = (('<a href="%s" target="_blank">Site</a>'
             '<br>'
             '<a href="%s" target="_blank">Directions</a>'
              '<br>'
              '<a href="%s" target="_blank">Record</a>')
             % (site_url, map_url, record_url))

    group = base
    icon_color = 'gray'
    if location_type in ['Activity', 'Attraction', 'Things To Do','Hiking']:
        group = activities
        icon_color = 'blue'
    if location_type in ['Dinner', 'Lunch', 'Breakfast/Coffee', 'Dining', 'Restaurant']:
        group = dining
        try:
            #Look for Gluten in the Features array
            if [s for s in fields['Features'] if "Gluten" in s]:
                icon = icon_map['GF Restaurant']
        except (KeyError):
            pass
        icon_color = 'red'
    if location_type in ['Bars', 'Winery', 'Brewery']:
        group = drinks
        icon_color = 'purple'
    if location_type in ['Travel']:
        group = travel
        icon_color = 'darkgreen'
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
map_.add_child(travel)

# Step 5: Add layer control to toggle the feature groups
folium.LayerControl().add_to(map_)

# Step 5: Save the map as an HTML file
file_path = "../output/folium_map.html"
map_.save(file_path)

# Step 6: Open the map in the default web browser on Mac
webbrowser.open('file://' + os.path.realpath(file_path))