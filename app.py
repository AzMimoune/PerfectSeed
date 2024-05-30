import warnings

import geopy
import joblib
import numpy as np
import openmeteo_requests
import pandas as pd
import requests_cache
from flask import Flask, render_template, request
from geopy.geocoders import Nominatim
from retry_requests import retry

warnings.filterwarnings('ignore')


def get_coordinates(city_name, country_name):
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


def get_precip_temp(longitude, latitude):
    # Set up the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": "2004-01-01",
        "end_date": "2024-01-01",
        "daily": ["weather_code", "temperature_2m_mean", "precipitation_sum"],
        "timezone": "auto",
        "hourly": "relative_humidity_2m"
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location
    response = responses[0]

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_weather_code = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_mean = daily.Variables(1).ValuesAsNumpy()
    daily_precipitation_sum = daily.Variables(2).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    ), "weather_code": daily_weather_code, "temperature_2m_mean": daily_temperature_2m_mean,
        "precipitation_sum": daily_precipitation_sum}
    hourly = response.Hourly()
    hourly_relative_humidity_2m = hourly.Variables(0).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=hourly.Interval()),
        inclusive="left"
    ), "relative_humidity_2m": hourly_relative_humidity_2m}

    hourly_dataframe = pd.DataFrame(data=hourly_data)
    h = np.mean(hourly_dataframe["relative_humidity_2m"])

    daily_dataframe = pd.DataFrame(data=daily_data)
    p = np.max(daily_dataframe["precipitation_sum"])
    t = np.max(daily_dataframe["temperature_2m_mean"])

    return p, t, h


def do_predict(array):
    # Load the model from the file
    model = joblib.load("static/model.pkl")

    # Make predictions using the loaded model
    pred = model.predict(array)

    return pred


app = Flask(__name__)
app.static_folder = 'static'


# Define routes and render HTML templates
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about-us')
def about_us():
    return render_template('about-us.html')


@app.route('/predict')
def predict():
    return render_template('predict.html')


@app.route('/submit', methods=['POST'])
def submit():
    nitrogen = float(request.form['n'])
    phosphorus = float(request.form['p'])
    potassium = float(request.form['k'])
    ph_level = float(request.form['ph'])
    wilaya = request.form['wilaya']
    long, lat = get_coordinates(wilaya, "Algeria")
    rain, temp, hum = get_precip_temp(long, lat)
    # rain = 202.94
    # temp = 20.88
    # hum = 82.01
    # Call your function to predict the crop
    pc = do_predict([[nitrogen, phosphorus, potassium, temp, hum, ph_level, rain]])[0]

    # Render the same template with the predicted crop
    return render_template('predict.html', predicted_crop=pc, show_modal='true')


if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)
