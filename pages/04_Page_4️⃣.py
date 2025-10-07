import streamlit as st
import pandas as pd
import os
import pymongo
import plotly.express as px

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
    opt = []
    for year in range(min_date.year, max_date.year+1):
        for month in range(1,13):
            opt.append(f"{year}-{month:02d}")
    sel = st.select_slider("Select a subset of months to display",
                           options = opt, value=(opt[0],opt[-1])) #create slider
    if sel:
        #extracting the range
        min,max = sel[0],sel[1]
        min_year,min_month = min.split("-")
        max_year,max_month = max.split("-")

        data_line = data_line[(data_line["starttime"] > pd.to_datetime(f"{min_year}-{min_month}-01")) &
                                (data_line["starttime"] < pd.to_datetime(f"{max_year}-{max_month}-01"))] #filter on selected date range


    # dates = st.date_input(
    #     "Select Date Range",
    #     value=(data_line["starttime"].min(), data_line["starttime"].max()),
    #     min_value=data_line["starttime"].min(),
    #     max_value=data_line["starttime"].max()
    # ) #date input widget
    # if len(dates) == 2:
    #     start_date, end_date = dates
    #     data_line = data_line[(data_line["starttime"] >= pd.to_datetime(start_date)) & 
    #                           (data_line["starttime"] <= pd.to_datetime(end_date))] #filter on selected date range
        
    fig2 = px.line(
        data_line,
        x="starttime",
        y="smooth",
        color="productiongroup",
        title="Daily Production (5-day MA)",
        labels={"starttime": "Date", "smooth": "Quantity (kWh)", "productiongroup": "Production Group"}
    ) #create line chart

    st.plotly_chart(fig2)

with st.expander("Data sources"):
    st.write(f'Elhub API https://api.elhub.no')