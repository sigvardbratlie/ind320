import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
st.title("CA1 - Page 2")

st.cache_data(show_spinner=False) #using cache data to only read in the first time. Spinner false as it disappears fast
def read_data(filepath):
    df = pd.read_csv(filepath)
    df["time"] = pd.to_datetime(df["time"]) #setting date feature to dtype datetime
    df = df.set_index("time") #Setting date feature as index
    return df

df = read_data("data/open-meteo-subset.csv") 

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