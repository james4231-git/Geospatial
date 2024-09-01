from pyairtable import Api
import requests
import json
import urllib.parse
import argparse

debug = True
test_count = 20

with open('../my_credentials.json') as f:
    credentials = json.loads(f.read())

# baseId = credentials['base']
key = credentials["key"]
Google_API_key = credentials['Google_API_Key']

def getPlaceJson(description):

    query_fields = '&fields=formatted_address%2Cname%2Crating%2Copening_hours%2Cgeometry%2Cplace_id'
    url = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json' + \
          '?input=' + description + \
          '&inputtype=textquery' + \
          query_fields +\
          '&key=' + Google_API_key

    response = requests.request("GET", url)
    response_json = response.json()

    candidates = response_json['candidates']
    if len(candidates) == 1:
        return candidates[0]
    else:
        print('Found %i candidates for %s' % (len(candidates), description))
        for candidate in candidates:
            print(candidate['formatted_address'])
            placeID_url = 'https://www.google.com/maps/place/?q=place_id:' + candidate['place_id']
            print(placeID_url)
            print(candidate)
        return None

def process_table(base,table_name,field_name):
    table = base.table(table_name)
    records = table.all()

    idx = 0
    for record in records:
        fields = record['fields']

        print("Processing %s" %(fields[field_name]))

        # Calculate airtable calculated field describing the record (e.g. name, town)
        Place_API_Encoding = fields['Place API Encoding']

        try:
            type = fields['Type']
        # except(ValueError):
        #     continue
        except(KeyError):
            continue

        if type[0] in ['Costs', 'Gift Idea']:
            #don't map these types
            print("Skipping %s of type %s" % (fields[field_name], type))
            continue

        # if Address isn't found (KeyError), retrieve data using the Google Place API
        try:
            # address = fields['Address']
            coordinates = fields['Coordinates']
            # print('%s address found: %s' % (fields['Item'], fields['Address']))
        except (KeyError):
            place_json = getPlaceJson(Place_API_Encoding)
            if place_json:
                # fields['Place API JSON'] = place_json
                address = place_json['formatted_address']
                location = place_json['geometry']['location']
                latitude = location['lat']
                longitude = location['lng']
                coordinates = ('%s, %s' % (latitude, longitude))
                # print('Updating %s address: %s' % (fields['Item'], address))
                print('Updating %s address: %s' % (fields[field_name], coordinates))
                table.update(record['id'],
                            {
                                'Place API JSON': str(place_json),
                                'Address': address,
                                'Coordinates': coordinates
                            }
                        )
            else:
                break
            idx += 1
        #if Place API JSON isn't found, use the address to look it up
        try:
            fields['Place API JSON']
        except (KeyError):
            place_json = getPlaceJson(urllib.parse.quote_plus(address))
            if place_json:
                # fields['Place API JSON'] = place_json
                print('Updating %s place json: %s' % (fields[field_name], str(place_json)))
                table.update(record['id'],
                            {'Place API JSON': str(place_json)}
                            )
            else:
                break
        if idx > test_count:
            break

# Function to get the BaseID by base name
def get_base_id_by_name(bases, base_name):
    for base in bases:
        if base.name == base_name:
            return base.id
    return None

def main():

    base_name= 'Travel'  # "James' Cheat Sheet"
    table_name = 'Vancouver & Banff'
    field_name = 'Item'

    # Initialize the argument parser
    parser = argparse.ArgumentParser(description="Retrieve records from a specified Airtable base and table.")

    # Adding optional arguments with default values defined in the entry point
    parser.add_argument("--Base", type=str, help="The name of the Airtable base")
    parser.add_argument("--Table", type=str, help="The name of the table in the Airtable base")
    parser.add_argument("--Field", type=str, help="The name of the primary field in the Airtable table")

    args = parser.parse_args()

    print(args.Base)

    if args.Base and args.Table:
        base_name = args.Base
        table_name = args.Table
        field_name = args.Field

    api = Api(key)
    bases = api.bases()
    baseId = get_base_id_by_name(bases, base_name)
    base = api.base(baseId)
    process_table(base, table_name, field_name)

if __name__ == "__main__":
    main()