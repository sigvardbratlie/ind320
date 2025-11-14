import streamlit as st
import pandas as pd
import os
import pymongo
import plotly.express as px
import calendar
from utilities import init, check_mongodb_connection,get_elhub_data,el_sidebar,sidebar_setup


# =========================================
#          FUNCTION DEFINITIONS & SETUP
# =========================================
init()
check_mongodb_connection()
st.set_page_config(layout="wide")
st.title("Elhub 🔋⚡️")
sidebar_setup("Electricity data analysis")
el_sidebar(disable_dataset_selection=True)
# =================================
#           DATA LOADING
# =================================
coordinates = st.session_state.get("location",{}).get("coordinates", None)
city = st.session_state.get("location",{}).get("city", None)
price_area = st.session_state.get("location",{}).get("price_area", "NO1")

data = get_elhub_data(st.session_state["client"], dataset=st.session_state.group.get("name"),dates = st.session_state.dates,filter_group=False,aggregate_group=False)

#st.markdown("### ELECTRICITY PRODUCTION DATA")
st.write("---")
cols = st.columns(2) #split into two columns
with cols[0]:
    st.markdown("## 🔋 Production by Group")        
    data_pie = data[data["pricearea"] == price_area] #select price area NO2
    data_pie = data_pie.groupby("productiongroup")["quantitykwh"].sum().reset_index() #create data

    fig = px.pie(
        data_pie,
        values="quantitykwh",
        names="productiongroup",
        title=f"Total Production by Group in {price_area}",
        hole=0.4
    ) #create pie chart

    st.plotly_chart(fig)

with cols[1]:
    st.markdown("## 📈 Production Over Time")
    data_line = data[data["pricearea"] == price_area] #continue with selected price area

    data_line = data_line.groupby(["productiongroup",
                            pd.Grouper(level = "starttime", freq="D")]
                                    )["quantitykwh"].sum().reset_index() #Aggregatate data for line plot. Same aggregation as in notebook
    
    if isinstance(st.session_state.group.get("values"), str):
        st.session_state.production_group = [st.session_state.production_group]
    data_line["smooth"] = data_line.groupby("productiongroup")["quantitykwh"]\
            .transform(lambda x: x.rolling(window=5, min_periods=1).mean()) #moving average with a window of 5 days
    data_line = data_line[data_line["productiongroup"].isin(st.session_state.group.get("values"))] #filter on selected production groups. default all groups


        
    fig2 = px.line(
        data_line,
        x="starttime",
        y="smooth",
        color="productiongroup",
        title="Daily Production (5-day MA)",
        labels={"starttime": "Date", "smooth": "Quantity (kWh)", "productiongroup": "Production Group"}
    ) #create line chart

    st.plotly_chart(fig2) #display line chart

with st.expander("Data sources"):
    st.write(f'Elhub API https://api.elhub.no')