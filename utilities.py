import streamlit as st
import pymongo
from dotenv import load_dotenv
import pandas as pd
import requests
import os
load_dotenv()


@st.cache_resource
def init_connection():
    return pymongo.MongoClient(st.secrets["mongo"]["uri"])

try:
    _client = init_connection()
    _client.admin.command('ping')
    st.sidebar.success("🔗 Connected to MongoDB")
except Exception as e:
    st.sidebar.error(f"Error connecting to MongoDB: {e}")
    st.stop()

# Pull data from the collection.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def get_data(_client):
    db = _client.elhub
    items = db.prod_data.find({})
    items = list(items)  # make hashable for st.cache_data
    data = pd.DataFrame(items)
    data.set_index("starttime", inplace=True)
    data.sort_index(inplace=True)
    data.drop(columns=["_id"], inplace=True)
    return data


# # ==== READING DATA ====
def mk_request(url: str,params: dict = None):
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

#Function for the API download
@st.cache_data(ttl=7200)
def get_weather(lat : float , lon:float, year : int, ):
    params = {"latitude" : lat, "longitude": lon, 
              "start_date": f"{year}-01-01",
              "end_date": f"{year}-12-31",
              "hourly": "temperature_2m,precipitation,wind_speed_10m,wind_gusts_10m_spread,wind_direction_10m",
              "models" : "era5"
              }
    base_url = "https://archive-api.open-meteo.com/v1/archive?"
    return mk_request(base_url,params=params)

def geocode(city : str):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=10&language=en&format=json"
    return mk_request(url)

@st.cache_data(ttl=7200)
def extract_coordinates(city: str):
    res = geocode(city).get("results")[0]
    lat, lon = res.get("latitude"), res.get("longitude")
    return lat, lon
