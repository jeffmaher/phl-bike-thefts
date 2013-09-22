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


def get_locations(latitude, longitude, mile_radius, start_date, end_date, start_hour, end_hour):
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

    if start_date and not end_date:
        locations = locations.filter(date__gte=start_date.date())
    elif start_date and end_date:
        locations = locations.filter(date__gte=start_date.date(), date__lte=end_date.date())
    elif end_date and not start_date:
        locations = locations.filter(date__lte=end_date.date())

    if start_hour and end_hour:
        locations = locations.filter(hour__gte=start_hour).filter(hour__lte=end_hour)

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
            "date": str(location.date),
            "stolen_value": location.stolen_value,
            "street_block": location.street_block,
            "hour": location.hour
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

        # date
        date_match = DATE_REGEX.match(props["THEFT_DATE"])
        year = int(date_match.group(1))
        month = int(date_match.group(2))
        day = int(date_match.group(3))
        hour = int(props["THEFT_HOUR"])
        location.date = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=0, second=0)

        # Hour
        location.hour = int(props["THEFT_HOUR"])

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

    # Validate starting date - not a required field, requires format is YY-MM-DD
    try:
        start_date = request.GET['start_date']
        start_date = datetime.datetime.strptime(start_date, '%y-%m-%d')
    except KeyError:
        start_date = None
    except ValueError:
        return HttpResponseBadRequest('Bad start date format - requires YY-MM-DD')

    # Validate ending date - not a required field, requires format is YY-MM-DD
    try:
        end_date = request.GET['end_date']
        end_date = datetime.datetime.strptime(end_date, '%y-%m-%d')
    except KeyError:
        end_date = None
    except ValueError:
        return HttpResponseBadRequest('Bad end date format - requires YY-MM-DD')


    # Validate starting hour - not a required field, attempts to convert to integer
    try:
        start_hour = request.GET['start_hour']
        start_hour = int(start_hour)
    except KeyError:
        start_hour = None
    except ValueError:
        return HttpResponseBadRequest('Non-numeric start hour parameter')



    # Validate ending hour - not a required field, attempts to convert to integer
    try:
        end_hour = request.GET['end_hour']
        end_hour = int(end_hour)
    except ValueError:
        return HttpResponseBadRequest('Non-numeric end hour parameter')
    except KeyError:
        end_hour = None

    if (start_hour and not end_hour) or (end_hour and not start_hour):
        return HttpResponseBadRequest("Requires both a start hour and end hour paramenter, or neither")



    locations = get_locations(latitude, longitude, radius, start_date, end_date, start_hour, end_hour)
    points = locations_to_points(locations)

    return json_response(points)