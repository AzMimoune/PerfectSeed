import requests
from datetime import datetime, timedelta

import geopy
from geopy.geocoders import Nominatim

# Replace these with your API key and the desired city and country
API_KEY = "d2afd3596b324c18bcf81731601d50e4"
CITY = "Tiaret"
COUNTRY = "Algeria"


def get_coordinates(city_name, country_name):
    """
    Returns the longitude and latitude coordinates of a city given its name and country.

    Args:
        city_name (str): The name of the city.
        country_name (str): The name of the country.

    Returns:
        tuple: A tuple containing the longitude and latitude coordinates as floats,
               or (None, None) if the location could not be found.
    """
    # Initialize the Nominatim geolocator
    geolocator = Nominatim(user_agent="my_app")

    # Construct the query string
    query = f"{city_name}, {country_name}"

    try:
        # Attempt to geocode the query
        location = geolocator.geocode(query)

        if location:
            # Return the coordinates
            return location.longitude, location.latitude
        else:
            print(f"No location found for {query}")
            return None, None
    except geopy.exc.GeocoderServiceError as e:
        print(f"Error: {e}")
        return None, None


# Base URL for the Weatherbit API
BASE_URL = "https://api.weatherbit.io/v2.0/history/daily"

# Calculate the start and end dates for the past year
today = datetime.now()
start_date = today - timedelta(days=365)
end_date = today


# Function to fetch historical weather data for a given date range
def fetch_historical_data(start, end):
    params = {
        "key": API_KEY,
        "city": CITY,
        "country": COUNTRY,
        # "start_date": start.strftime("%Y-%m-%d"),
        # "end_date": end.strftime("%Y-%m-%d"),
        "start_date": "2016-10-01",
        "end_date": "2017-10-01"
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    return data["data"]


# Fetch historical data for the past year
historical_data = fetch_historical_data(start_date, end_date)

# Calculate the average rainfall
total_rainfall = sum(day["precip"] for day in historical_data)
average_rainfall = total_rainfall / len(historical_data)

print(f"Average rainfall for the past year in {CITY}, {COUNTRY}: {average_rainfall} mm")
