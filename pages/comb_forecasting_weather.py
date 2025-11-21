"""
Electricity Supply/Demand Forecasting with Weather Data Page

SARIMAX forecasting of electricity data using weather variables as exogenous inputs.
Allows users to select SARIMAX parameters and visualize forecast results with confidence intervals.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
from utilities import (
    init, sidebar_setup, get_elhub_data, init_connection,
    el_sidebar, get_weather_data, extract_coordinates
)
import streamlit as st
import plotly.graph_objects as go
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.impute import SimpleImputer

# =========================================
#          FUNCTION DEFINITIONS & SETUP
# =========================================
@st.cache_data(ttl=600)
def sarimax_forecast(
    x_data: pd.DataFrame,
    y_data: pd.Series,
    start_idx: int,
    end_idx: int,
    ar: int = 1,
    diff: int = 1,
    ma: int = 1,
    seasonal_diff: int = 1,
    seasonal_ma: int = 1,
    seasonal_ar: int = 1,
    seasonal_period: int = 12
) -> tuple:
    """
    Perform SARIMAX forecasting with exogenous variables.

    Args:
        x_data: DataFrame with exogenous variables.
        y_data: Target time series to forecast.
        start_idx: Index where training data starts.
        end_idx: Index where training data ends.
        ar: Autoregressive order.
        diff: Differencing order.
        ma: Moving average order.
        seasonal_ar: Seasonal autoregressive order.
        seasonal_diff: Seasonal differencing order.
        seasonal_ma: Seasonal moving average order.
        seasonal_period: Length of the seasonal cycle.

    Returns:
        Tuple of (forecast object, confidence intervals DataFrame, forecast values).
    """
    mod = sm.tsa.statespace.SARIMAX(
        y_data.iloc[start_idx:end_idx], 
        exog=x_data.iloc[start_idx:end_idx],
        order=(ar,diff,ma), 
        seasonal_order=(seasonal_ar,seasonal_diff,seasonal_ma,seasonal_period)
    )
    res = mod.fit(disp=False)
    
    steps = len(y_data) - end_idx
    forecast = res.forecast(steps=steps, exog=x_data.iloc[end_idx:])
    
    # For confidence intervals
    predict_dy = res.get_forecast(steps=steps, exog=x_data.iloc[end_idx:])
    predict_dy_ci = predict_dy.conf_int()
    
    return predict_dy, predict_dy_ci, forecast

st.title("Electricity Supply/Demand Forecasting 📈")
init()
init_connection()
sidebar_setup(disable_location=True)
el_sidebar(disable_group=True)

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


# =========================================
#         RESAMPLE DATA
# =========================================
resample = st.radio("Resample data", options = ["Hourly", "Daily", "Weekly", "Monthly"], index=2,horizontal=True)
if resample != "Hourly":
    if resample == "Daily":
        df_m = df_m.resample('D').mean()
    elif resample == "Weekly":
        df_m = df_m.resample('W').mean()
    elif resample == "Monthly":
        df_m = df_m.resample('M').mean()


# =========================================
#          PARAMETER SELECTION
# =========================================
trainin_time = st.select_slider("Select timeframe for training", options = df_m.index.sort_values().unique(), value=(df_m.index.min(), df_m.index[int(len(df_m)*0.7)]))
cols = st.columns(3)
param_names = ["AR", "differentiation", "MA"]
params = []
for i, col in enumerate(cols):
    with col:
        params.append(st.number_input(param_names[i], min_value=0, max_value=5, value=1, step=1))

cols =  st.columns(4)
season_param_names = ["Seasonal AR", "Seasonal differentiation", "Seasonal MA", "Seasonal period"]
season_params = []
for i, col in enumerate(cols):
    with col:
        if season_param_names[i] == "Seasonal period":
            season_params.append(st.number_input(season_param_names[i], min_value=1, max_value=24, value=12, step=1))
        else:
            season_params.append(st.number_input(season_param_names[i], min_value=1, max_value=24, value=1, step=1))


cols = st.columns(2)
y = cols[0].selectbox("Select target variable for forecasting", options=df_m.columns, index=0)
x = cols[1].multiselect("Select feature variables for forecasting (Exog)", options=df_m.columns.drop(y), default=df_m.columns.drop(y).tolist())

ci = st.toggle("Show Confidence Intervals", value=False)


# =========================================
#          FORECASTING
# =========================================

start_idx = df_m.index.get_loc(trainin_time[0])
end_idx = df_m.index.get_loc(trainin_time[1])
y_data = df_m[y]
x_data = df_m[x]


imputer = SimpleImputer(strategy='mean') 
x_data[:] = imputer.fit_transform(x_data) #impute to handle missing values

predict_dy, predict_dy_ci, forecast = sarimax_forecast(x_data, y_data, start_idx, end_idx,
                                                       *params, *season_params) #forecast
#metrics
st.write(f'MEAN Squared Error: {mean_squared_error(y_data.iloc[end_idx:].values, forecast.values):.2f} ')
st.write(f'R2 Score: {r2_score(y_data.iloc[end_idx:].values, forecast.values):.2f} ')

# Plot
fig = go.Figure()
fig.add_trace(go.Scatter(x=y_data.index, y=y_data, name='Actual'))
fig.add_trace(go.Scatter(x=y_data.index[start_idx:end_idx], y=y_data.iloc[start_idx:end_idx], name='Training', line=dict(color='blue'), opacity=0.7))
fig.add_trace(go.Scatter(x=y_data.index[end_idx:], y=forecast, name='Forecast', line=dict(color = "red"), opacity=0.7))

#Confidence intervals
if ci:
    fig.add_trace(go.Scatter(x=y_data.index[end_idx:], y=predict_dy_ci.iloc[:, 0], name='Lower CI', line=dict(width=0), showlegend=False))                    
    fig.add_trace(go.Scatter(x=y_data.index[end_idx:], y=predict_dy_ci.iloc[:, 1], name='Upper CI', fill='tonexty', line=dict(width=0)))
                            
st.plotly_chart(fig, use_container_width=True)

with st.expander("Data sources"):
    st.write(f'Meteo API https://archive-api.open-meteo.com')
    st.write(f'Elhub API https://api.elhub.no')