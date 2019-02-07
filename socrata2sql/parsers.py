from datetime import datetime
import json


def parse_datetime(str_val):
    if str_val == '':
        return None

    try:
        # Socrata >=2.1
        return datetime.strptime(str_val, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        # Socrata <2.1
        return datetime.strptime(str_val, "%Y-%m-%dT%H:%M:%S")


def parse_geom(geo_data):
    if geo_data is None:
        return None

    if 'latitude' in geo_data and 'longitude' in geo_data:
        return 'SRID=4326;POINT(%s %s)' % (
            geo_data['latitude'],
            geo_data['longitude'],
        )
    elif 'human_address' in geo_data and 'latitude' not in geo_data:
        return None

    if geo_data['type'] == 'Point':
        return 'SRID=4326;POINT(%s %s)' % (
            geo_data['coordinates'][0],
            geo_data['coordinates'][1],
        )

    raise NotImplementedError('%s are not yet supported' % geo_data['type'])


def parse_str(raw_str):
    if isinstance(raw_str, dict):
        if 'url' in raw_str:
            return raw_str['url']

        return json.dumps(raw_str)

    return raw_str
