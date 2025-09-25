import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("CA1 - Page 3")

# ==== READING DATA ====
st.cache_data(show_spinner=False) #same as page 2
def read_data(filepath):
    df = pd.read_csv(filepath)
    df["time"] = pd.to_datetime(df["time"])
    df = df.set_index("time")
    return df
df = read_data("data/open-meteo-subset.csv")
# === PREPARING DATA ===
df = (df-df.mean())/df.std() #Normalize the data

# === SETUP OPTIONS === 
start_end = "E" #choosing either end or start with "E" or "S". Defualt "E", no option implemented
date_agg_map = {"Year":f"Y{start_end}",f"Month":f"M{start_end}",f"Week":f"W",f"Day":f"D"} #a map for choosing the correct label from streamlit radio widget

plot_type = st.selectbox("Choose plot type",options=["line","bar","hist"]) #selection for plot type as no specific type is specified in the task description.

# === PLOTTING ===
if plot_type == "line":
    months_select = st.select_slider("Select a subset of months to display",options = range(1,13), value=(1,12)) #creating the slider widget for selecting month range
    months = list(range(months_select[0],months_select[1]+1)) #adding one as python index is zero-based
    y = st.multiselect("Select columns to plot",options = df.columns) #Selection of y
    y = y if y else df.columns #ensuring that y is not None
    date_agg = st.radio("Choose date aggregation",  options=["Month","Week","Day"],index = 1,horizontal=True) #adding data aggregation option
    st.line_chart(df.loc[df.index.month.isin(months),y].resample(date_agg_map[date_agg]).mean()) #creating the line chart
                
    
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
