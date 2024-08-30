from pyairtable import Api
import requests
import json
import urllib.parse

debug = True

import json
from pyairtable import Api

def getPlaceJson(description):

    fields = '&fields=formatted_address%2Cname%2Crating%2Copening_hours%2Cgeometry%2Cplace_id'
    url = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json' + \
          '?input=' + description + \
          '&inputtype=textquery' + \
          fields +\
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

if __name__ == '__main__':

    with open('../my_credentials.json') as f:
        credentials = json.loads(f.read())

    baseId = credentials['base']
    key = credentials["key"]
    Google_API_key = credentials['Google_API_Key']

    # Get base
    # base = Airtable(baseId, key)
    # table = 'Vancouver & Banff'
    # records = base.get(table)
    api = Api(key)
    base = api.base(baseId)
    table = base.table('Vancouver & Banff')
    records = table.all()

    test_count = 10
    idx = 0
    for record in records:
        fields = record['fields']
        Place_API_Encoding = fields['Place API Encoding']

        try:
            type = fields['Type']
        # except(ValueError):
        #     continue
        except(KeyError):
            continue

        if type in ['Costs']:
            #don't map these types
            print("Skipping %s of type %s" % (fields['Item'], type))
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
                print('Updating %s address: %s' % (fields['Item'], coordinates))
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
                print('Updating %s place json: %s' % (fields['Item'], str(place_json)))
                table.update(record['id'],
                            {'Place API JSON': str(place_json)}
                            )
            else:
                break
        if idx > test_count:
            break