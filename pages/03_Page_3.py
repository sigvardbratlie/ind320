import streamlit as st
import pandas as pd
from utilities import get_weather, geocode, extract_coordinates

st.set_page_config(layout="wide")
st.title("Weather Data")


lat,lon = extract_coordinates("Bergen")
data = get_weather(lat, lon, 2019)

df = pd.DataFrame(data.get("hourly"))
df["time"] = pd.to_datetime(df["time"])
df.set_index("time", inplace=True)

# === CREATING TABLE
fy,fm = df.sort_index().index[0].year, df.sort_index().index[0].month #extracting the first month from the data

first_month = df.loc[(df.index.year == fy) & df.index.month == fm, :] #filtering only on the first month
first_month = (first_month - first_month.mean()) / first_month.std() #normalize for comparison

data_for_editor = []
for col in first_month.columns:
    data_for_editor.append({
        "column": col,
        "data": first_month[col].tolist(), 
    }) #creating the data container for LineChartColumn

st.data_editor(
    data_for_editor,
    column_config={
        "column": st.column_config.TextColumn(
            "Måling (Enhet)",
            width="medium",
        ),
        "data": st.column_config.LineChartColumn(
           "data",
           width="large",
           help="",
           y_min=first_month.min().min(),
           y_max=first_month.max().max()
        ),
    },
    use_container_width=True,
    hide_index=True
) #Creating the widget LineChartColumn showing data for the first month
