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
    #st.session_state.setdefault("price_area", "NO1")
    st.session_state.setdefault("start_date", datetime.datetime(2021,1,1))
    st.session_state.setdefault("end_date", datetime.datetime(2024,12,31))
    st.session_state.setdefault("production_group", ["hydro","wind","solar","thermal","other"])
    st.session_state.setdefault("consumption_group", ['secondary', 'primary','tertiary', 'cabin',  'household'])
    st.session_state.setdefault("dataset", "production")
    st.session_state.setdefault("location", {"city": "Oslo", 
                                             "coordinates": (59.9139, 10.7522), 
                                             "price_area": "NO1"})

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
        locations = {"Oslo" : "NO1", 
                "Kristiansand" : "NO2", 
                "Trondheim" : "NO3", 
                "Tromsø" : "NO4", 
                "Bergen" : "NO5"}
        options = [f"{v} ({k})" for k,v in locations.items()]
        
        dates = st.date_input("Select Date Range",
                              value=(start_date, end_date),
                              min_value="2021-01-01",
                              max_value="2024-12-31",
                              )
        price_area = st.session_state.get("location",{}).get("price_area")
        city = st.session_state.get("location",{}).get("city")
        default_option = f"{price_area} ({city})"
        #price_area = st.radio("Select Price Area", options=price_area_options,index = price_area_options.index(st.session_state.price_area.strip()),horizontal=True,) 
        location = st.selectbox("Select price area", options=options, index=options.index(default_option)) #price_area_options.index(st.session_state.get("location",{}).get("price_area", "NO1")))

        if location:
            city = location.split("(")[1].replace(")","").strip()
            price_area = location.split("(")[0].strip()

            coord = extract_coordinates(city)
            st.session_state.location = {"city": city, 
                                        "price_area": price_area,
                                        "coordinates": coord}

        if len(dates) == 2 and dates[1]>=dates[0]:
            st.session_state.dates = dates
        else:
            if len(dates) != 2:
                st.error("Please select both start and end dates.")
            elif dates[1]<dates[0]:
                st.error("End date must be after start date.")
            else:
                st.error("Invalid date selection.")


def el_sidebar(disable_dataset_selection: bool = False, 
               radio_group: bool = False):
    with st.sidebar:
        dataset = st.selectbox("Select production or consumption data", options=["production","consumption"], index=0, disabled=disable_dataset_selection)
        #year = st.selectbox("Select Year", options=[2019, 2020, 2021, 2022, 2023], index=0)
        prod_group = None
        cons_group = None
        if dataset == "production":
            if radio_group:
                prod_group = st.radio("Select Production Group",
                                    options=["hydro","wind","solar","thermal","other"],
                                    index=0,
                                    horizontal=True) #widget for selecting production groups
            else:
                prod_group = st.pills("Select Production Group",
                                    options=["hydro","wind","solar","thermal","other"],
                                    selection_mode="multi",
                                    default = st.session_state.production_group) #widget for selecting production groups
            if prod_group:
                st.session_state.production_group = prod_group
        elif dataset == "consumption":
            if radio_group:
                cons_group = st.radio("Select Consumption Group",
                                    options=['secondary', 'primary', 'tertiary', 'cabin', 'household'],
                                    index=0,
                                    horizontal=True) #widget for selecting consumption groups
            else:
                cons_group = st.pills("Select Consumption Group",
                                    options=['secondary', 'primary', 'tertiary', 'cabin', 'household'],
                                    selection_mode="multi",
                                    default = st.session_state.consumption_group) #widget for selecting consumption groups
            if cons_group:
                st.session_state.consumption_group = cons_group
            
        if cons_group or prod_group:
            st.session_state.dataset = dataset
        



