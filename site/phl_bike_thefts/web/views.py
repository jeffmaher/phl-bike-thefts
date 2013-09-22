from django.shortcuts import render_to_response, render
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponseNotFound, HttpResponseBadRequest
import json
import requests
import re
import datetime

from models import TheftLocation

# Regex for matching date info
DATE_REGEX = re.compile(r'(\d{4})-(\d\d)-(\d\d)')

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