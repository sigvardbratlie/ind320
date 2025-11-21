# Imports
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from utilities import init, sidebar_setup,get_elhub_data,init_connection,el_sidebar,get_weather_data,extract_coordinates
import streamlit as st
import plotly.graph_objects as go
from sklearn.metrics import r2_score,mean_squared_error
from sklearn.impute import SimpleImputer

# =========================================
#          FUNCTION DEFINITIONS & SETUP
# =========================================
@st.cache_data(ttl=600)
def sarimax_forecast(x_data, y_data, start_idx, end_idx):
    mod = sm.tsa.statespace.SARIMAX(
        y_data.iloc[start_idx:end_idx], 
        exog=x_data.iloc[start_idx:end_idx],
        order=(1,1,1), 
        seasonal_order=(1,1,1,12)
    )
    res = mod.fit(disp=False)
    
    steps = len(y_data) - end_idx
    forecast = res.forecast(steps=steps, exog=x_data.iloc[end_idx:])
    
    # For confidence intervals
    predict_dy = res.get_forecast(steps=steps, exog=x_data.iloc[end_idx:])
    predict_dy_ci = predict_dy.conf_int()
    
    return predict_dy, predict_dy_ci, forecast
init()
init_connection()
sidebar_setup("map")
el_sidebar()

# =========================================
#          LOAD DATA
# =========================================

df_el = get_elhub_data(st.session_state["client"],
                       dataset=st.session_state.group.get("name"),
                       dates = st.session_state.dates,
                       filter_group=True,
                       aggregate_group=True,)
df_w = get_weather_data(coordinates=st.session_state.get("location",{}).get("coordinates"),
                        dates = st.session_state.dates, 
                        set_time_index=True,)


df_m = pd.merge(df_el, df_w, left_index=True, right_index=True, how='inner')
#st.dataframe(df_m.head())

trainin_time = st.select_slider("Select timeframe for training", options = df_m.index.sort_values().unique(), value=(df_m.index.min(), df_m.index[int(len(df_m)*0.7)]))
cols = st.columns(2)
y = cols[0].selectbox("Select target variable for forecasting", options=df_m.columns, index=0)
x = cols[1].multiselect("Select feature variables for forecasting (Exog)", options=df_m.columns.drop(y), default=df_m.columns.drop(y).tolist())

# =========================================
#          FORECASTING
# =========================================

start_idx = df_m.index.get_loc(trainin_time[0])
end_idx = df_m.index.get_loc(trainin_time[1])
y_data = df_m[y]
x_data = df_m[x]


imputer = SimpleImputer(strategy='mean') 
x_data[:] = imputer.fit_transform(x_data) #impute to handle missing values

predict_dy, predict_dy_ci, forecast = sarimax_forecast(x_data, y_data, start_idx, end_idx) #forecast

#metrics
st.write(f'MEAN Squared Error: {mean_squared_error(y_data.iloc[end_idx:].values, forecast.values):.2f} ')
st.write(f'R2 Score: {r2_score(y_data.iloc[end_idx:].values, forecast.values):.2f} ')

# Plot
fig = go.Figure()
fig.add_trace(go.Scatter(x=y_data.index, y=y_data, name='Actual'))
fig.add_trace(go.Scatter(x=y_data.index[start_idx:end_idx], y=y_data.iloc[start_idx:end_idx], name='Training', line=dict(color='blue'), opacity=0.7))
fig.add_trace(go.Scatter(x=y_data.index[end_idx:], y=forecast, name='Forecast', line=dict(dash='dash'), opacity=0.7))
st.plotly_chart(fig, use_container_width=True)