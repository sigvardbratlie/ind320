import streamlit as st
import pandas as pd
from datetime import datetime
from utilities import get_weather_data,extract_coordinates,init, sidebar_setup
import plotly.graph_objects as go
import plotly.express as px

# =========================================
#          DEFINE FUNCTIONS & SETUP
# =========================================
init()
st.set_page_config(layout="wide")
st.title("Weather Data 🌡️☁️")
sidebar_setup("weather data analysis")


# =================================
#           DATA LOADING
# =================================
coordinates = st.session_state.get("location",{}).get("coordinates", None)
city = st.session_state.get("location",{}).get("city", None)
price_area = st.session_state.get("location",{}).get("price_area", "NO1")

df  = get_weather_data(coordinates=coordinates, dates = st.session_state.dates, set_time_index=True)


# === SETUP OPTIONS === 
start_end = "E" #choosing either end or start with "E" or "S". Defualt "E", no option implemented
date_agg_map = {"Year":f"Y{start_end}",f"Month":f"M{start_end}",f"Week":f"W",f"Day":f"D"} #a map for choosing the correct label from streamlit radio widget

cols = st.columns(2)
with cols[0]:
    plot_type = st.radio("Choose plot type",options=["line","bar","hist"],horizontal=True) #selection for plot type as no specific type is specified in the task description.
with cols[1]:
    norm = st.toggle("Normalize data",value=False) #toggle for normalization

if norm:
    # === PREPARING DATA ===
    df = (df-df.mean())/df.std() #Normalize the data

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

        line_to_plot = df.loc[(df.index > datetime(year = int(min_year),month = int(min_month),day = 1))
                             & (df.index < datetime(year = int(max_year),month = int(max_month),day = 1)),
                             y].resample(date_agg_map[date_agg]).mean()
                      
        
        fig = px.line(line_to_plot, x=line_to_plot.index, y=y) #creating line plot

        st.plotly_chart(fig) #creating the line chart


elif plot_type == "bar":
    x = st.selectbox("Select which column to use as x-axis", options=df.columns) #selecting values for x
    y = st.multiselect("Select columns to plot",options = df.columns) #selecting values for y
    y = y if y else df.columns.tolist() #ensuring that y is not None

    #fig.add_trace(go.Bar(x=df[x], y=df[y[0]], name=y[0])) #adding bar trace
    #fig.update_layout(barmode='group')
    fig = px.bar(df, x=x, y=y, barmode='group') #create bar plot
    st.plotly_chart(fig) #plot data


elif plot_type == "hist":
    x = st.selectbox("Select which column to use as x-axis", options=df.columns) #selecting values for x
    x = x if x else df.columns[0] #ensuring x is not None
    fig = px.histogram(df, x=x, nbins=100) #create histogram
    st.plotly_chart(fig) #plot data