"""
Utility functions for the Electricity and Weather Data Dashboard.

This module provides shared functions for data loading, MongoDB connection,
sidebar setup, and API requests used across the Streamlit application.
"""
import streamlit as st
import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv
import pandas as pd
import requests
import os
import datetime
from typing import Literal, Optional

load_dotenv()


@st.cache_resource
def init_connection() -> MongoClient:
    """Initialize and cache the MongoDB connection."""
    return pymongo.MongoClient(st.secrets["mongo"]["uri"])


def init() -> None:
    """Initialize session state with default values for client, dates, group, and location."""
    st.session_state['client'] = init_connection()
    st.session_state.setdefault("dates", (datetime.datetime(2021,1,1), datetime.datetime(2024,12,31)))
    st.session_state.setdefault("group", {"name" : "production", 
                                          "feat_name" : "productiongroup",
                                          "values" : ["hydro","wind","solar","thermal","other"]})
    st.session_state.setdefault("location", {"city": "Oslo", 
                                             "coordinates": (59.9139, 10.7522), 
                                             "price_area": "NO1"})
    

@st.cache_data(ttl=600)
def check_mongodb_connection() -> None:
    """Verify MongoDB connection and display status in sidebar."""
    try:
        st.session_state["client"].admin.command('ping')
        st.sidebar.success("🔗 Connected to MongoDB")
    except Exception as e:
        st.sidebar.error(f"Error connecting to MongoDB: {e}")
        st.stop()

@st.cache_data(ttl=600, show_spinner=False)
def get_elhub_data(
    _client: MongoClient,
    dataset: Literal["production", "consumption"] = "production",
    dates: tuple[datetime.datetime, datetime.datetime] = (datetime.datetime(2024, 1, 1), datetime.datetime(2024, 12, 31)),
    filter_group: bool = False,
    aggregate_group: bool = False,
    set_time_index: bool = True,
) -> pd.DataFrame:
    """
    Fetch electricity data from MongoDB.

    Args:
        _client: MongoDB client connection.
        dataset: Type of data to fetch ('production' or 'consumption').
        dates: Tuple of (start_date, end_date) for filtering.
        filter_group: Whether to filter by production/consumption group.
        aggregate_group: Whether to aggregate data by timestamp.
        set_time_index: Whether to set starttime as the DataFrame index.

    Returns:
        DataFrame containing the electricity data.
    """
    
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
        raise ValueError("dataset must be either 'production' or 'consumption'")
    
    with st.spinner("Fetching data from electricity data from database..."):
        data = pd.DataFrame(list(items))
        if set_time_index:
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

def mk_request(url: str, params: Optional[dict] = None) -> Optional[dict]:
    """
    Make a GET request to the specified URL.

    Args:
        url: The API endpoint URL.
        params: Optional query parameters.

    Returns:
        JSON response as a dictionary, or None if request fails.
    """
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

@st.cache_data(ttl=7200, show_spinner=False)
def get_weather_data(
    coordinates: tuple[float, float],
    dates: tuple[datetime.datetime, datetime.datetime],
    set_time_index: bool = True
) -> pd.DataFrame:
    """
    Fetch weather data from the Open-Meteo API.

    Args:
        coordinates: Tuple of (latitude, longitude).
        dates: Tuple of (start_date, end_date).
        set_time_index: Whether to set time as the DataFrame index.

    Returns:
        DataFrame containing weather data.
    """
    lat, lon = coordinates
    params = {"latitude" : lat, "longitude": lon, 
              "start_date": dates[0].strftime("%Y-%m-%d"),
              "end_date": dates[1].strftime("%Y-%m-%d"),
              "hourly": "temperature_2m,precipitation,wind_speed_10m,wind_gusts_10m_spread,wind_direction_10m",
              "models" : "era5"
              }
    base_url = "https://archive-api.open-meteo.com/v1/archive?"
    with st.spinner("Fetching weather data from API..."):
        response = mk_request(base_url,params=params)
        if response:
            df_w = pd.DataFrame(response.get("hourly"))
            df_w["time"] = pd.to_datetime(df_w["time"])
            if set_time_index:
                return df_w.set_index("time")
            return df_w
        st.warning("No weather data retrieved from API.")
        return pd.DataFrame()

def geocode(city: str) -> Optional[dict]:
    """
    Geocode a city name to coordinates using the Open-Meteo geocoding API.

    Args:
        city: Name of the city to geocode.

    Returns:
        JSON response with geocoding results, or None if request fails.
    """
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=10&language=en&format=json"
    return mk_request(url)


@st.cache_data(ttl=7200)
def extract_coordinates(city: str) -> tuple[float, float]:
    """
    Extract latitude and longitude from geocoding results.

    Args:
        city: Name of the city.

    Returns:
        Tuple of (latitude, longitude).
    """
    res = geocode(city).get("results")[0]
    lat, lon = res.get("latitude"), res.get("longitude")
    return lat, lon


def select_price_area(disable_location: bool = False) -> None:
    """
    Display price area selector in sidebar and update session state.

    Args:
        disable_location: Whether to disable the selector.
    """
    options = ["NO1","NO2","NO3","NO4","NO5"]
    price_area = st.selectbox("Select price area", 
                              options=options, 
                              index=options.index(st.session_state.get("location").get("price_area")),
                              disabled=disable_location)
    if price_area:
        st.session_state.location["price_area"] = price_area

def select_city(disable_location: bool = False) -> None:
    """
    Display city selector in sidebar and update session state.

    Args:
        disable_location: Whether to disable the selector.
    """
    locations = {"Oslo" : "NO1", 
                "Kristiansand" : "NO2", 
                "Trondheim" : "NO3", 
                "Tromsø" : "NO4", 
                "Bergen" : "NO5"}
    city = st.selectbox("Select city", options=list(locations.keys()), index=None, disabled=disable_location)
    if city:
        st.session_state.location["city"] = city
        st.session_state.location["price_area"] = locations.get(city)
        coord = extract_coordinates(city)
        st.session_state.location["coordinates"] = coord
                          
def sidebar_setup(start_date: str = "2024-01-01", end_date: str = "2024-12-31", disable_location: bool = False) -> None:
    """
    Set up the sidebar with navigation links and control widgets.

    Args:
        start_date: Default start date for date picker.
        end_date: Default end date for date picker.
        disable_location: Whether to disable location selectors.
    """
    with st.sidebar:
        # =========================
        #     SIDEBAR NAVIGATION
        # =========================
        st.page_link(page="main.py", label="🏠 Home")
        with st.expander("⚡️ Electricity Data Analysis", expanded=False):
            st.page_link(page="pages/el_prod.py",label = "⚡️ Production data")
            st.page_link(page="pages/el_stl_spect.py",label = "🔋 STL Decomposition & Spectrogram")
            st.page_link(page="pages/el_forecasting.py",label = "📈 Supply/Demand Forecasting")
        with st.expander("☁️ Weather Data Analysis", expanded=False):
            st.page_link(page="pages/weather_plots.py",label = "🌦️ Weather Data Plots")
            st.page_link(page="pages/weather_lof.py",label = "🌡️ Outlier Detection & LOF Analysis")
        with st.expander("🌡️⚡️ Weather and Electricity Analysis", expanded=False):
            st.page_link(page="pages/comb_map.py",label = "🗺️❄️ Electricity Data Map & snow drift")
            st.page_link(page="pages/comb_forecasting_weather.py",label = "📈 Supply/Demand Forecasting with weather data (Bonus)")
            
            st.page_link(page="pages/comb_corr.py",label = "🔗 Correlation Analysis between Weather and Electricity Data")
        
        #st.info(infotxt)

        #==========================
        #     SIDEBAR CONTROLS
        #==========================
        dates = st.date_input("Select Date Range",
                              value=(start_date, end_date),
                              min_value="2021-01-01",
                              max_value="2024-12-31",
                              )
        select_price_area(disable_location=disable_location)
        select_city(disable_location=disable_location)

        if len(dates) == 2 and dates[1]>=dates[0]:
            st.session_state.dates = dates
        else:
            if len(dates) != 2:
                st.error("Please select both start and end dates.")
            elif dates[1]<dates[0]:
                st.error("End date must be after start date.")
            else:
                st.error("Invalid date selection.")


def el_sidebar(
    disable_dataset_selection: bool = False,
    radio_group: bool = False,
    disable_group: bool = False,
) -> None:
    """
    Set up electricity data selectors in the sidebar.

    Args:
        disable_dataset_selection: Whether to disable dataset selection (production/consumption).
        radio_group: Whether to use radio buttons instead of pills for group selection.
        disable_group: Whether to disable group selection.
    """
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
                                    default = default,
                                    disabled=disable_group
                                    ) #widget for selecting production groups
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
                
        check_mongodb_connection()
            
        



