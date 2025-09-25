import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")
st.title("CA1 - Page 2")

st.cache_data(show_spinner=False)
def read_data(filepath):
    df = pd.read_csv(filepath)
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time")
    return df

df = read_data("data/open-meteo-subset.csv")

fy,fm = df.index.min().year, df.index.min().month
first_month = df.loc[(df.index.year == fy) & df.index.month == fm, :]

first_month = (first_month - first_month.mean()) / first_month.std()


data_for_editor = []
for col in first_month.columns:
    data_for_editor.append({
        "column": col,
        "data": first_month[col].tolist(), 
    })

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
)