from django.db import models

# Create your models here.


class TheftLocation(models.Model):

    # Comments include the names from the original data set

    # DC_KEY: The unique identifier of the crime that consists of Year + District + Unique
    crime_key = models.CharField(max_length=30)

    # DC_NUM: The unique crime identifier
    crime_id = models.CharField(max_length=30)

    # UCR: The Uniform Crime Reports code.
    # 615: value >= $200
    # 625: $50 <= value < $200
    # 635: value < $50
    crime_code = models.IntegerField()

    # DC_DIST: A two character field that identifies the district boundary
    district_boundary = models.CharField(max_length=2)

    # Time of theft: Combination of the following fields form the original data
    # THEFT_DATE: The date of the theft (ISO 8601 format)
    # THEFT_YEAR: The year of the theft
    # THEFT_HOUR: The hour of the theft
    date = models.DateTimeField()

    #Hour of theft as in integer, used for filtering
    hour = models.IntegerField()

    # STOLEN_VAL: The value in dollars of the bicycle stolen
    stolen_value = models.IntegerField()

    # LAT: Latitude of crime location
    latitude = models.DecimalField(max_digits=20, decimal_places=17)

    # LNG: Longitude of crime location
    longitude = models.DecimalField(max_digits=20, decimal_places=17)

    # LOCATION_B: The location of crime generalized by street block
    street_block = models.CharField(max_length=200)

