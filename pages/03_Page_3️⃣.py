import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("CA1 - Page 3")


st.cache_data(show_spinner=False)
def read_data(filepath):
    df = pd.read_csv(filepath)
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time")
    return df

df = read_data("data/open-meteo-subset.csv")
df = (df-df.mean())/df.std()

start_end = "E"
date_agg_map = {"Year":f"Y{start_end}",f"Month":f"M{start_end}",f"Week":f"W",f"Day":f"D"}

plot_type = st.selectbox("Choose plot type",options=["line","bar","hist"])

if plot_type == "line":
    months_select = st.select_slider("Select a subset of months to display",options = range(1,13), value=(1,12))
    months = list(range(months_select[0],months_select[1]+1))
    y = st.multiselect("Select columns to plot",options = df.columns)
    y = y if y else df.columns
    date_agg = st.radio("Choose date aggregation",  options=["Month","Week","Day"],index = 1,horizontal=True)
    #st.info(f'month : {months, months_select}, y : {y}, date_agg : {date_agg}')
    st.line_chart(df.loc[df.index.month.isin(months),y].resample(date_agg_map[date_agg]).mean()
                )
    
elif plot_type == "bar":
    x = st.selectbox("Select which column to use as x-axis", options=df.columns)
    x = x #if x else df.columns[0]
    y = st.multiselect("Select columns to plot",options = df.columns)
    y = y if y else df.columns.tolist()
    st.bar_chart(data = df, x = x, y = y)

elif plot_type == "hist":
    x = st.selectbox("Select which column to use as x-axis", options=df.columns)
    x = x if x else df.columns[0]
    data = df.value_counts(x)
    st.bar_chart(data)
