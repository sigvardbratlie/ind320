import streamlit as st
import pandas as pd
import os
import pymongo
import plotly.express as px
import calendar

st.set_page_config(layout="wide")


# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return pymongo.MongoClient(st.secrets["mongo"]["uri"])

try:
    client = init_connection()
    client.admin.command('ping')
    st.sidebar.success("🔗 Connected to MongoDB")
except Exception as e:
    st.sidebar.error(f"Error connecting to MongoDB: {e}")
    st.stop()

# Pull data from the collection.
# Uses st.cache_data to only rerun when the query changes or after 10 min.
@st.cache_data(ttl=600)
def get_data():
    db = client.elhub
    items = db.prod_data.find({})
    items = list(items)  # make hashable for st.cache_data
    return items

items = get_data()
data = pd.DataFrame(items)


st.markdown("# ELECTRICITY PRODUCTION DATA")
st.write("---")

cols = st.columns(2) #split into two columns
with cols[0]:
    st.markdown("## 🔋 Production by Group")

    price_area = st.radio(
        "Select Price Area",
        options=data["pricearea"].sort_values().unique().tolist(),
        horizontal=True,
        index=1,
        label_visibility="collapsed"
    )

    if price_area:
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
    
    prod_group = st.pills(
        "Select Production Group",
        options=data["productiongroup"].sort_values().unique().tolist(),
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