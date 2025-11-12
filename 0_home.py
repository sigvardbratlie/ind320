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
    st.page_link(page="pages/06_map.py",label = "🗺️ Electricity Data Map")