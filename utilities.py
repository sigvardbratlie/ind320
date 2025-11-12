import streamlit as st
import pymongo
from dotenv import load_dotenv
import pandas as pd
import requests
import os
import datetime
load_dotenv()


@st.cache_resource
def init_connection():
    return pymongo.MongoClient(st.secrets["mongo"]["uri"])

@st.cache_data(ttl=600)
def check_mongodb_connection():
    try:
        st.session_state["client"].admin.command('ping')
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


def init():
    st.session_state['client'] = init_connection()
    st.session_state.setdefault("price_area", "NO2")
    st.session_state.setdefault("start_date", datetime.date(2021,1,1))
    st.session_state.setdefault("end_date", datetime.date(2024,12,31))
    st.session_state.setdefault("production_group", "hydro")


def sidebar_setup(infotxt : str,start_date : str = "2021-01-01", end_date : str = "2024-12-31"):
    with st.sidebar:
        st.info(infotxt)
        dates = st.date_input("Select Date Range",
                              value=(start_date, end_date),
                              min_value=start_date,
                              max_value=end_date,
                              )
        price_area_options = ["NO1","NO2","NO3","NO4","NO5"]
        price_area = st.radio("Select Price Area", options=price_area_options,index = price_area_options.index(st.session_state.price_area.strip()),
                              horizontal=True,) 
        st.session_state.price_area = price_area

        if len(dates) != 2:
            st.error("Please select a start and end date.")
        if dates[0] > dates[1]:
            st.error("Start date must be before end date.")
        else:  
            st.session_state.start_date = dates[0]
            st.session_state.end_date = dates[1]
        

def weather_sidebar():
    with st.sidebar:
        st.info("Weather data")
        city = st.selectbox("Select City", options=["Bergen", "Oslo", "Trondheim", "Tromsø"], index=0)
        year = st.selectbox("Select Year", options=[2019, 2020, 2021, 2022, 2023], index=0)
        st.session_state.city = city
        st.session_state.year = year

def el_sidebar():
    with st.sidebar:
        st.info("Electricity data")
        year = st.selectbox("Select Year", options=[2019, 2020, 2021, 2022, 2023], index=0)
        prod_group = st.radio("Select Production Group",
            options=["hydro","wind","solar","thermal","other"],index=0,horizontal=True,) #widget for selecting production groups
        st.session_state.year = year
        st.session_state.production_group = prod_group
