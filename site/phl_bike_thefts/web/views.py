from django.shortcuts import render_to_response, render
import json
import requests
import re
import datetime
from django.http import HttpResponse, Http404, HttpResponseBadRequest, \
    HttpRequest, HttpResponseServerError, HttpResponseNotAllowed
from models import TheftLocation


# --- Helper Functions ---
# Regex for matching date info
DATE_REGEX = re.compile(r'(\d{4})-(\d\d)-(\d\d)')

MILE_PER_DEGREE_LATITUDE = (1.0 / 69.0)
MILE_PER_DEGREE_LONGITUDE = (1.0 / 49.0) # Approximate, since this changes depending on how far North or South, 49 is at 45 degress (or halfway between equator and poles)


def json_response(response_obj):
    response = []
    if response_obj:
        response = json.dumps(response_obj)
    else:
        response = json.dumps(response)
    return HttpResponse(response, mimetype='application/json', content_type='application/json; charset=utf8')


def get_locations(latitude, longitude, mile_radius):
    latitude_diff = mile_radius * MILE_PER_DEGREE_LATITUDE
    upper_bound_latitude = latitude + latitude_diff
    lower_bound_latitude = latitude - latitude_diff

    longitude_diff = mile_radius * MILE_PER_DEGREE_LONGITUDE
    upper_bound_longitude = longitude + longitude_diff
    lower_bound_longitude = longitude - longitude_diff

    locations = TheftLocation.objects.filter(latitude__lte=upper_bound_latitude,
                                        latitude__gte=lower_bound_latitude,
                                        longitude__lte=upper_bound_longitude,
                                        longitude__gte=lower_bound_longitude)
    return locations


def location_to_point(location):
    point = {
        "type": "Point",
        "coordinates": [float(location.latitude), float(location.longitude)],
        "properties": {
            "id": location.id,
            "crime_id": location.crime_key,
            "crime_code": location.crime_code,
            "district_boundary": location.district_boundary,
            "moment": str(location.moment),
            "stolen_value": location.stolen_value,
            "street_block": location.street_block
        }
    }

    return point


def locations_to_points(locations):
    points = []
    for location in locations:
        points.append(location_to_point(location))

    return points
# --- View Rendering Functions ---


# Create your views here.
def index(request):
    return render_to_response("index.html")


def refresh(request):
    raw_data = requests.get("https://raw.github.com/CityOfPhiladelphia/phl-open-geodata/master/bicycle_thefts/bicycle_thefts.geojson")
    thefts = json.loads(raw_data.text)["features"]

    locations = []

    for theft in thefts:
        location = TheftLocation()

        location.latitude = theft["geometry"]["coordinates"][1]
        location.longitude = theft["geometry"]["coordinates"][0]

        props = theft["properties"]
        location.crime_code = props["UCR"]
        location.crime_id = props["DC_NUM"]
        location.crime_key = props["DC_KEY"]
        location.district_boundary = props["DC_DIST"]
        location.street_block = props["LOCATION_B"]
        location.stolen_value = props["STOLEN_VAL"]

        # Moment
        date_match = DATE_REGEX.match(props["THEFT_DATE"])
        year = int(date_match.group(1))
        month = int(date_match.group(2))
        day = int(date_match.group(3))
        hour = int(props["THEFT_HOUR"])
        location.moment = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=0, second=0)

        locations.append(location)

    TheftLocation.objects.all().delete()
    TheftLocation.objects.bulk_create(locations)

    return render_to_response("refresh.html")


def search(request):
        # Validate request - must be GET
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])

    # Validate latitude - required, number only
    try:
        latitude = request.GET['latitude']
        latitude = float(latitude)
    except KeyError:
        return HttpResponseBadRequest('Missing latitude parameter')
    except ValueError:
        return HttpResponseBadRequest('Non-numeric latitude parameter')

    # Validate longitude - required number only
    try:
        longitude = request.GET['longitude']
        longitude = float(longitude)
    except KeyError:
        return HttpResponseBadRequest('Missing longitude parameter')
    except ValueError:
        return HttpResponseBadRequest('Non-numeric longitude parameter')

    # Validate radius - required, number only
    try:
        radius = request.GET['radius']
        radius = float(radius)
    except KeyError:
        return HttpResponseBadRequest('Missing radius parameter')
    except ValueError:
        return HttpResponseBadRequest('Non-numeric radius parameter')

    locations = get_locations(latitude, longitude, radius)
    points = locations_to_points(locations)

    return json_response(points)