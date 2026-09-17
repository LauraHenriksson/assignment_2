import json
import os
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd
import streamlit as st


# Configure the browser tab and use a wide layout for the dashboard.
st.set_page_config(page_title="Weather Explorer", page_icon="🌦️", layout="wide")

# Cities shown in the sidebar by default.
DEFAULT_CITIES = ["Aalborg", "Copenhagen", "London", "New York", "Tokyo"]


def get_api_key():
	# Read the key from Streamlit Cloud secrets or a local environment variable.
	try:
		return st.secrets.get("OPENWEATHER_API_KEY", "")
	except (FileNotFoundError, KeyError):
		return os.getenv("OPENWEATHER_API_KEY", "")


@st.cache_data(ttl=600)
def fetch_weather(city, units):
	# Build the URL and ask OpenWeatherMap for the current weather.
	query = urlencode({"q": city, "appid": get_api_key(), "units": units})
	request_url = f"https://api.openweathermap.org/data/2.5/weather?{query}"
	with urlopen(request_url, timeout=10) as response:
		return json.load(response)


@st.cache_data(ttl=600)
def fetch_forecast(city, units):
	# Request weather data in three-hour steps for the next five days.
	query = urlencode({"q": city, "appid": get_api_key(), "units": units})
	request_url = f"https://api.openweathermap.org/data/2.5/forecast?{query}"
	with urlopen(request_url, timeout=10) as response:
		return json.load(response)


def temperature_unit(units):
	return "°C" if units == "metric" else "°F"


def weather_error(city, error):
	if isinstance(error, HTTPError):
		if error.code == 401:
			return "The OpenWeatherMap API key was rejected."
		if error.code == 404:
			return f"Could not find weather data for {city}."
		return f"OpenWeatherMap returned an error ({error.code})."
	return "The weather service could not be reached. Try again later."


def load_current_weather(cities, units):
	# Try each selected city so one failed request does not stop the dashboard.
	weather = []
	errors = []
	for city in cities:
		try:
			weather.append(fetch_weather(city, units))
		except (HTTPError, URLError, TimeoutError) as error:
			errors.append(weather_error(city, error))
	return weather, errors


def weather_table(weather, units):
	# Convert the API response into rows that are easy to display in a table.
	unit = temperature_unit(units)
	return pd.DataFrame(
		[
			{
				"City": f"{item['name']}, {item['sys']['country']}",
				"Condition": item["weather"][0]["description"].title(),
				f"Current ({unit})": item["main"]["temp"],
				f"Feels like ({unit})": item["main"]["feels_like"],
				f"Low ({unit})": item["main"]["temp_min"],
				f"High ({unit})": item["main"]["temp_max"],
				"Humidity (%)": item["main"]["humidity"],
				"Wind (m/s)": item["wind"]["speed"],
			}
			for item in weather
		]
	)


st.title("Weather Explorer")
st.caption("Compare live conditions and explore the next five days.")

if not get_api_key():
	st.error("Add OPENWEATHER_API_KEY to Streamlit secrets or your environment before using the app.")
	st.stop()

# Sidebar controls let the user choose units, cities, and a forecast location.
with st.sidebar:
	st.header("Dashboard settings")
	units_label = st.radio("Temperature unit", ["Celsius", "Fahrenheit"])
	units = "metric" if units_label == "Celsius" else "imperial"
	selected_cities = st.multiselect(
		"Cities to compare",
		DEFAULT_CITIES,
		default=["Aalborg", "Copenhagen", "London"],
	)
	forecast_city = st.text_input("Forecast city", value="Aalborg").strip()
	if st.button("Refresh data"):
		fetch_weather.clear()
		fetch_forecast.clear()
		st.rerun()
	st.caption("Data is cached for 10 minutes.")

if not selected_cities:
	st.info("Choose at least one city in the sidebar to load weather data.")
	st.stop()

weather, errors = load_current_weather(selected_cities, units)
# Show a warning for any city that could not be loaded.
for error in errors:
	st.warning(error)

if not weather:
	st.error("No weather data could be loaded.")
	st.stop()

unit = temperature_unit(units)
# Tabs separate the current weather, comparisons, and forecast views.
overview_tab, comparison_tab, forecast_tab = st.tabs(
	["Current overview", "Compare cities", "Five-day forecast"]
)

with overview_tab:
	# Show one summary card for each selected city.
	st.subheader("Current conditions")
	metric_columns = st.columns(min(len(weather), 4))
	for column, item in zip(metric_columns, weather):
		with column:
			st.metric(
				f"{item['name']}, {item['sys']['country']}",
				f"{item['main']['temp']:.1f}{unit}",
				f"Feels like {item['main']['feels_like']:.1f}{unit}",
			)
			st.write(item["weather"][0]["description"].title())

	st.dataframe(
		weather_table(weather, units),
		hide_index=True,
		use_container_width=True,
	)

with comparison_tab:
	# Use bar charts to compare temperatures between the selected cities.
	st.subheader("Temperature comparison")
	comparison_data = weather_table(weather, units).set_index("City")
	st.bar_chart(comparison_data[[f"Current ({unit})", f"Feels like ({unit})"]])
	st.subheader("Daily range")
	st.bar_chart(comparison_data[[f"Low ({unit})", f"High ({unit})"]])

with forecast_tab:
	st.subheader(f"Forecast for {forecast_city or 'your city'}")
	if not forecast_city:
		st.info("Enter a city in the sidebar to see its forecast.")
	else:
		try:
			# Load the forecast only when this tab has a city to display.
			forecast = fetch_forecast(forecast_city, units)
		except (HTTPError, URLError, TimeoutError) as error:
			st.error(weather_error(forecast_city, error))
		else:
			# Extract the useful forecast values from each three-hour record.
			forecast_rows = []
			for item in forecast["list"]:
				forecast_rows.append(
					{
						"Date": datetime.fromtimestamp(item["dt"]).date(),
						"Temperature": item["main"]["temp"],
						"Minimum": item["main"]["temp_min"],
						"Maximum": item["main"]["temp_max"],
						"Condition": item["weather"][0]["description"].title(),
					}
				)
			forecast_data = pd.DataFrame(forecast_rows)
			# Group the three-hour records into daily minimum, average, and maximum values.
			daily_forecast = forecast_data.groupby("Date", as_index=False).agg(
				Temperature=("Temperature", "mean"),
				Minimum=("Minimum", "min"),
				Maximum=("Maximum", "max"),
			)
			daily_forecast = daily_forecast.set_index("Date")
			st.line_chart(daily_forecast)
			st.dataframe(
				forecast_data.style.format(
					{
						"Temperature": f"{{:.1f}}{unit}",
						"Minimum": f"{{:.1f}}{unit}",
						"Maximum": f"{{:.1f}}{unit}",
					}
				),
				hide_index=True,
				use_container_width=True,
			)

st.caption(
		"Last checked: "
		f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} local time"
)
