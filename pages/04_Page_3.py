import streamlit as st
import pandas as pd
from datetime import datetime
import os
import requests
from utilities import get_weather,extract_coordinates,init


# =========================================
#          DEFINE FUNCTIONS & SETUP
# =========================================
init()
st.set_page_config(layout="wide")
st.title("Weather Data 🌡️☁️")

# =================================
#           DATA LOADING
# =================================
lat,lon = extract_coordinates("Bergen")
data = get_weather(lat, lon, 2019)
df = pd.DataFrame(data.get("hourly"))
df["time"] = pd.to_datetime(df["time"])
df.set_index("time", inplace=True)

# === PREPARING DATA ===
df = (df-df.mean())/df.std() #Normalize the data

# === SETUP OPTIONS === 
start_end = "E" #choosing either end or start with "E" or "S". Defualt "E", no option implemented
date_agg_map = {"Year":f"Y{start_end}",f"Month":f"M{start_end}",f"Week":f"W",f"Day":f"D"} #a map for choosing the correct label from streamlit radio widget

plot_type = st.selectbox("Choose plot type",options=["line","bar","hist"]) #selection for plot type as no specific type is specified in the task description.

# === PLOTTING ===
if plot_type == "line":
    date_agg = st.radio("Choose date aggregation",  options=["Month","Week","Day"],index = 1,horizontal=True) #adding data aggregation option
    df_line = df.resample(date_agg_map[date_agg]).mean()
    #print(df_line.index.tolist(), type(df_line.index.tolist()[0]))
    opt = [f"{year}-{month}" for year,month in zip(df_line.index.year,df_line.index.month)] #create all possible options
    sel = st.select_slider("Select a subset of months to display",options = opt, value=(opt[0],opt[-1])) #create slider
    if sel:
        #extracting the range
        min,max = sel[0],sel[1]
        (min_year),(min_month) = min.split("-")
        (max_year),(max_month) = max.split("-")

        y = st.multiselect("Select columns to plot",options = df.columns) #Selection of y
        y = y if y else df.columns #ensuring that y is not None
        st.line_chart(df.loc[(df.index > datetime(year = int(min_year),month = int(min_month),day = 1))
                             & (df.index < datetime(year = int(max_year),month = int(max_month),day = 1)),
                             y]
                      .resample(date_agg_map[date_agg]).mean()) #creating the line chart
                
    
elif plot_type == "bar":
    x = st.selectbox("Select which column to use as x-axis", options=df.columns) #selecting values for x
    x = x #if x else df.columns[0]
    y = st.multiselect("Select columns to plot",options = df.columns) #selecting values for y
    y = y if y else df.columns.tolist() #ensuring that y is not None
    st.bar_chart(data = df, x = x, y = y) #creating the bar chart

elif plot_type == "hist":
    x = st.selectbox("Select which column to use as x-axis", options=df.columns) #selecting values for x
    x = x if x else df.columns[0] #ensuring x is not None
    data = df.value_counts(x) #mk data
    st.bar_chart(data) #plot data
