import requests
import json
import urllib.parse
from airtable_class import Table, get_parser

debug = False
test_count = 20

with open('../my_credentials.json') as f:
    credentials = json.loads(f.read())
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

def process_table(table,field_name):

    idx = 0
    for record in table.records:

        fields = record.fields

        if debug:
            print("Processing %s" %(fields[field_name]))

        # Calculate airtable calculated field describing the record (e.g. name, town)
        Place_API_Encoding = fields['Place API Encoding']

        try:
            type = fields['Type']
        # except(ValueError):
        #     continue
        except(KeyError):
            continue

        if type in ['Costs', 'Gift Idea']:
            #don't map these types
            if debug:
                print("Skipping %s of type %s" % (fields[field_name], type))
            continue

        # if Address isn't found (KeyError), retrieve data using the Google Place API
        missing_address = False
        missing_coords = False
        missing_JSON = False
        try:
            address = fields['Address']
        except (KeyError):
            missing_address = True
        try:
            coordinates = fields['Coordinates']
        except (KeyError):
            missing_coords = True
            # if Place API JSON isn't found, use the address to look it up
        try:
            fields['Place API JSON']
        except (KeyError):
            missing_JSON = True

        if missing_address or missing_coords or missing_JSON:
            print("Looking up %s" %(fields[field_name]))

            if not missing_address:
                #use the address that has been provided
                Place_API_Encoding = urllib.parse.quote_plus(address)

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
                record.update(
                            {
                                'Place API JSON': str(place_json),
                                'Address': address,
                                'Coordinates': coordinates
                            }
                        )
            else:
                print(record.get_url())
                break
            idx += 1
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
    parser = get_parser()
    args = parser.parse_args()

    if args.Base and args.Table:
        base_name = args.Base
        table_name = args.Table
        field_name = args.Field

    table = Table(base_name,table_name)
    process_table(table, field_name)

if __name__ == "__main__":
    main()