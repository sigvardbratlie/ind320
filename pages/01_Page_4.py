import streamlit as st
import pandas as pd
import os
import pymongo
import plotly.express as px
import calendar
from utilities import init, check_mongodb_connection,get_data


# =========================================
#          FUNCTION DEFINITIONS & SETUP
# =========================================
init()
check_mongodb_connection()
st.set_page_config(layout="wide")
st.title("Elhub 🔋⚡️")

# =================================
#           DATA LOADING
# =================================
data = get_data(st.session_state["client"])

#st.markdown("### ELECTRICITY PRODUCTION DATA")
st.write("---")

cols = st.columns(2) #split into two columns
with cols[0]:
    st.markdown("## 🔋 Production by Group")

    #retrieve previous selection from session state
    price_area = st.session_state.get('price_area', 'NO2') 
    pa_options = data["pricearea"].sort_values().unique().tolist()
    pa_idx = pa_options.index(price_area) if price_area in pa_options else 1

    price_area = st.radio(
        "Select Price Area",
        options=pa_options,
        horizontal=True,
        index=pa_idx,
        label_visibility="collapsed"
    )

    if price_area:
        st.session_state['price_area'] = price_area #store selection in session state
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
    if price_area:
        data_pa = data[data["pricearea"] == price_area] #continue with selected price area
    
    pd_options = data["productiongroup"].sort_values().unique().tolist()
    
    prod_group = st.pills(
        "Select Production Group",
        options=pd_options,
        selection_mode= "multi"
    ) #widget for selecting production groups
    
    data_line = data_pa.groupby(["productiongroup",
                            pd.Grouper(key="starttime", 
                                    freq="D")])["quantitykwh"].sum().reset_index() #Aggregatate data for line plot. Same aggregation as in notebook
    
    data_line["smooth"] = data_line.groupby("productiongroup")["quantitykwh"]\
            .transform(lambda x: x.rolling(window=5, min_periods=1).mean()) #moving average with a window of 5 days
    if prod_group:
        data_line = data_line[data_line["productiongroup"].isin(prod_group)] #filter on selected production groups. default all groups

    #month slider. Reuse from CA1
    min_date = data_line["starttime"].min().date()
    max_date = data_line["starttime"].max().date()
    
    
    month = st.selectbox("Select Month to Display",
                            options = calendar.month_name[1:],
                            index=0,
                            label_visibility="collapsed"
    ) #widget for selecting month

    if month:
        month = list(calendar.month_name).index(month) #get month number from name
        data_line = data_line[data_line["starttime"].dt.month == month] #filter on selected months
        
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