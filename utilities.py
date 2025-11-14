import streamlit as st
import pymongo
from dotenv import load_dotenv
import pandas as pd
import requests
import os
import datetime
from typing import Literal
load_dotenv()


@st.cache_resource
def init_connection():
    return pymongo.MongoClient(st.secrets["mongo"]["uri"])

def init():
    st.session_state['client'] = init_connection()
    st.session_state.setdefault("dates", (datetime.datetime(2021,1,1), datetime.datetime(2024,12,31)))
    st.session_state.setdefault("group", {"name" : "production", 
                                          "feat_name" : "productiongroup",
                                          "values" : ["hydro","wind","solar","thermal","other"]})
    st.session_state.setdefault("location", {"city": "Oslo", 
                                             "coordinates": (59.9139, 10.7522), 
                                             "price_area": "NO1"})
    

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
                   filter_group : bool = False,
                   aggregate_group : bool = False
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

    if filter_group:
        feat_name = st.session_state.group.get("feat_name")
        values = st.session_state.group.get("values")
        data = data[data[feat_name].isin(values)]


    if aggregate_group:
        data = data.groupby(data.index)['quantitykwh'].sum().reset_index().set_index("starttime").sort_index()

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
def get_weather_data(coordinates,dates : tuple,set_time_index: bool = True) -> pd.DataFrame:
    lat, lon = coordinates
    params = {"latitude" : lat, "longitude": lon, 
              "start_date": dates[0].strftime("%Y-%m-%d"),
              "end_date": dates[1].strftime("%Y-%m-%d"),
              "hourly": "temperature_2m,precipitation,wind_speed_10m,wind_gusts_10m_spread,wind_direction_10m",
              "models" : "era5"
              }
    base_url = "https://archive-api.open-meteo.com/v1/archive?"
    response = mk_request(base_url,params=params)
    if response:
        df_w = pd.DataFrame(response.get("hourly"))
        df_w["time"] = pd.to_datetime(df_w["time"])
        if set_time_index:
            return df_w.set_index("time")
        return df_w
    st.warning("No weather data retrieved from API.")
    return pd.DataFrame()

def geocode(city : str):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=10&language=en&format=json"
    return mk_request(url)

@st.cache_data(ttl=7200)
def extract_coordinates(city: str):
    res = geocode(city).get("results")[0]
    lat, lon = res.get("latitude"), res.get("longitude")
    return lat, lon


def select_price_area():
    options = ["NO1","NO2","NO3","NO4","NO5"]
    price_area = st.selectbox("Select price area", options=options, index=options.index(st.session_state.get("location").get("price_area")))
    if price_area:
        st.session_state.location["price_area"] = price_area

def select_city():
    locations = {"Oslo" : "NO1", 
                "Kristiansand" : "NO2", 
                "Trondheim" : "NO3", 
                "Tromsø" : "NO4", 
                "Bergen" : "NO5"}
    city = st.selectbox("Select city", options=list(locations.keys()), index=None)
    if city:
        st.session_state.location["city"] = city
        st.session_state.location["price_area"] = locations.get(city)
        coord = extract_coordinates(city)
        st.session_state.location["coordinates"] = coord
                          
def sidebar_setup(infotxt : str,start_date : str = "2024-01-01", end_date : str = "2024-12-31"):
    with st.sidebar:
        st.info(infotxt)
        dates = st.date_input("Select Date Range",
                              value=(start_date, end_date),
                              min_value="2021-01-01",
                              max_value="2024-12-31",
                              )
        select_price_area()
        select_city()

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
            options = ["hydro","wind","solar","thermal","other"]
            default = st.session_state.group.get("values") if st.session_state.group.get("values") in options else ["hydro","wind","solar","thermal","other"]
            if radio_group:
                prod_group = st.radio("Select Production Group",
                                    options=options,
                                    index=0,
                                    horizontal=True) #widget for selecting production groups
            else:
                prod_group = st.pills("Select Production Group",
                                    options=options,
                                    selection_mode="multi",
                                    default = default) #widget for selecting production groups
            if prod_group:
                st.session_state.group = {"name" : "production", 
                                         "feat_name" : "productiongroup",
                                         "values" : prod_group}
        elif dataset == "consumption":
            options = ['secondary', 'primary', 'tertiary', 'cabin', 'household']
            default = st.session_state.group.get("values") if st.session_state.group.get("values") in options else ['secondary', 'primary', 'tertiary', 'cabin', 'household']
            if radio_group:
                cons_group = st.radio("Select Consumption Group",
                                    options=options,
                                    index=0 ,
                                    horizontal=True) #widget for selecting consumption groups
            else:
                cons_group = st.pills("Select Consumption Group",
                                    options=options,
                                    selection_mode="multi",
                                    default = default) #widget for selecting consumption groups
            if cons_group:
                st.session_state.group = {"name" : "consumption", 
                                         "feat_name" : "consumptiongroup",
                                         "values" : cons_group}
            
        



