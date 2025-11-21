import streamlit as st
from utilities import init, sidebar_setup

init()

st.set_page_config(layout="wide") #setting page conig with layout wide to fill the page
sidebar_setup("Home")


st.title("Electricity and Weather Data Dashboard ⚡️🌡️")


cols = st.columns(2) #split into two columns
with cols[0]:
    st.subheader("Electricity Data")
    st.page_link(page="pages/01_🔋⚡️ Production.py",label = "🔋⚡️ Production data")
    st.page_link(page="pages/02_🔋⚡️ STL & spectrogram.py",label = "🔋⚡️ STL Decomposition & Spectrogram")

with cols[1]:
    st.subheader("Weather Data")
    st.page_link(page="pages/04_🌡️☁️  Plots.py",label = "🌡️☁️ Weather Data Plots")
    st.page_link(page="pages/05_🌡️☁️ Outliers & LOF.py",label = "🌡️☁️ Outlier Detection & LOF Analysis")


cols = st.columns(2)
with cols[0]:
    st.subheader("Map Visualization")
    st.page_link(page="pages/06_Map & snow drift.py",label = "🗺️ Electricity Data Map")

with cols[1]:
    st.subheader("Forecasting and correlation analysis")
    st.page_link(page="pages/08_Forecasting.py",label = "📈 Electricity Supply/Demand Forecasting")
    st.page_link(page="pages/07_Meteorology & energy production.py",label = "🔗 Correlation Analysis between Weather and Electricity Data")