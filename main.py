import streamlit as st
from utilities import init, sidebar_setup
import os

init()

st.set_page_config(layout="wide") #setting page conig with layout wide to fill the page
sidebar_setup()


st.title("Electricity and Weather Data Dashboard ⚡️🌡️")


cols = st.columns(3) #split into two columns
with cols[0]:
    st.subheader("⚡️ Electricity Data Analysis")
    st.write(
        """
        This dashboard provides an interactive platform to explore and analyze electricity production and consumption data alongside weather data. 
        Utilize the sidebar to customize your data selection, including date ranges, locations, and specific data groups.
        """
    )
    st.page_link(page="pages/el_prod.py",label = "⚡️ Production data")
    st.page_link(page="pages/el_stl_spect.py",label = "🔋 STL Decomposition & Spectrogram")
    st.page_link(page="pages/el_forecasting.py",label = "📈 Supply/Demand Forecasting")

with cols[1]:
    st.subheader("Weather Data analysis 🌡️☁️")
    st.write(
        '''
        Explore comprehensive weather data analyses, including visualizations, outlier detection, and correlations with electricity data.
        Use the sidebar to select your location and date range for tailored insights.'''
    )
    st.page_link(page="pages/weather_plots.py",label = "🌦️ Weather Data Plots")
    st.page_link(page="pages/weather_lof.py",label = "🌡️ Outlier Detection & LOF Analysis")

with cols[2]:
    st.subheader("Weather and Electricity Analysis")
    st.write(
        '''
        This section combines weather and electricity data to provide insights into their interactions. 
        Analyze correlations, visualize data on maps, and forecast electricity supply and demand based on weather conditions.
        '''
    )
    st.page_link(page="pages/comb_map.py",label = "🗺️❄️ Electricity Data Map & snow drift")
    st.page_link(page="pages/comb_forecasting_weather.py",label = "📈 Supply/Demand Forecasting with Weather (Bonus)")
    st.page_link(page="pages/comb_corr.py",label = "🔗 Correlation Analysis between Weather and Electricity Data")

