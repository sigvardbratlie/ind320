import streamlit as st
import pymongo
from dotenv import load_dotenv
import pandas as pd
import requests
import os
import datetime
from typing import Literal
load_dotenv()



def init():
    st.session_state['client'] = init_connection()
    st.session_state.setdefault("price_area", "NO2")
    st.session_state.setdefault("start_date", datetime.datetime(2021,1,1))
    st.session_state.setdefault("end_date", datetime.datetime(2024,12,31))
    st.session_state.setdefault("production_group", ["hydro","wind","solar","thermal","other"])
    st.session_state.setdefault("dataset", "production")

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
def get_elhub_data(_client,
                   dataset : Literal["production","consumption"]= "production",
                   dates : tuple = (datetime.datetime(2024,1,1),datetime.datetime(2024,12,31)),
                   ) -> pd.DataFrame:
    if isinstance(dates[0], datetime.date) or isinstance(dates[1], datetime.date):
        dates = (datetime.datetime.combine(dates[0], datetime.time()),
                 datetime.datetime.combine(dates[1], datetime.time()))
    if not isinstance(dates[0], datetime.datetime):
        raise ValueError("dates[0] must be a datetime.date or datetime.datetime object")

    db = _client.elhub
    if dataset == "production":
        items = db.prod_data.find({"starttime": {"$gte": dates[0], "$lte": dates[1]}})
    elif dataset == "consumption":
        items = db.cons_data.find({"starttime": {"$gte": dates[0], "$lte": dates[1]}})
    else:
        raise ValueError("dataset must be either 'prod' or 'cons'")
    
    data = pd.DataFrame(list(items))
    data.set_index("starttime", inplace=True)
    data.sort_index(inplace=True)
    data.drop(columns=["_id"], inplace=True,errors='ignore')
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
def get_weather_data(lat : float , lon:float, dates : tuple):
    params = {"latitude" : lat, "longitude": lon, 
              "start_date": dates[0].strftime("%Y-%m-%d"),
              "end_date": dates[1].strftime("%Y-%m-%d"),
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




def sidebar_setup(infotxt : str,start_date : str = "2024-01-01", end_date : str = "2024-12-31"):
    with st.sidebar:
        st.info(infotxt)
        dates = st.date_input("Select Date Range",
                              value=(start_date, end_date),
                              min_value="2021-01-01",
                              max_value="2024-12-31",
                              )
        price_area_options = ["NO1","NO2","NO3","NO4","NO5"]
        price_area = st.radio("Select Price Area", options=price_area_options,index = price_area_options.index(st.session_state.price_area.strip()),
                              horizontal=True,) 
        st.session_state.price_area = price_area

        if len(dates) == 2 and dates[1]>=dates[0]:
            st.session_state.dates = dates
        else:
            if len(dates) != 2:
                st.error("Please select both start and end dates.")
            elif dates[1]<dates[0]:
                st.error("End date must be after start date.")
            else:
                st.error("Invalid date selection.")
            
        

def weather_sidebar():
    with st.sidebar:
        city = st.selectbox("Select City", options=["Bergen", "Oslo", "Trondheim", "Tromsø"], index=0)
        #year = st.selectbox("Select Year", options=[2019, 2020, 2021, 2022, 2023], index=0)
        st.session_state.city = city
        #st.session_state.year = year

def el_sidebar(disable_dataset_selection: bool = False):
    with st.sidebar:
        dataset = st.selectbox("Select production or consumption data", options=["production","consumption"], index=0, disabled=disable_dataset_selection)
        #year = st.selectbox("Select Year", options=[2019, 2020, 2021, 2022, 2023], index=0)
        prod_group = st.pills("Select Production Group",
                              options=["hydro","wind","solar","thermal","other"],
                              selection_mode="multi") #widget for selecting production groups
        if prod_group:
            st.session_state.production_group = prod_group
        st.session_state.dataset = dataset
