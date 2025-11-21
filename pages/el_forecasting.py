"""
Electricity Supply/Demand Forecasting Page

SARIMAX forecasting of electricity production/consumption data.
Allows users to select SARIMAX parameters, exogenous variables, and visualize forecasts.
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
    Perform SARIMAX forecasting on electricity data.

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
sidebar_setup()
el_sidebar(radio_group=True)

# =========================================
#          LOAD DATA
# =========================================

df = get_elhub_data(st.session_state["client"],
                       dataset=st.session_state.group.get("name"),
                       dates = st.session_state.dates,
                       filter_group=False,
                       aggregate_group=False,
                       set_time_index=True
                       )

cols = ["productiongroup" , "pricearea"] if st.session_state.group.get("name") == "production" else ["consumptiongroup" , "pricearea"]
df = pd.pivot_table(df, index=df.index, columns=cols, values='quantitykwh')

# =========================================
#         RESAMPLE DATA
# =========================================
resample = st.radio("Resample data", options = ["Hourly", "Daily", "Weekly", "Monthly"], index=1,horizontal=True)
if resample != "Hourly":
    if resample == "Daily":
        df = df.resample('D').mean()
    elif resample == "Weekly":
        df = df.resample('W').mean()
    elif resample == "Monthly":
        df = df.resample('M').mean()

# =========================================
#          PARAMETER SELECTION
# =========================================
trainin_time = st.select_slider("Select timeframe for training", options = df.index.sort_values().unique(), value=(df.index.min(), df.index[int(len(df)*0.7)]))

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

cols = st.columns(3)
group_options = df.columns.get_level_values(0).unique().tolist()
pricearea_options = df.columns.get_level_values(1).unique().tolist()
with cols[0]:
    st.markdown("### Select target variable and options:")
    group = st.selectbox("Select group", options=group_options)
    pricearea = st.selectbox("Select price area", options=pricearea_options)
    st.session_state.group["values"] = group
    st.session_state.location["price_area"] = pricearea
with cols[1]:
    st.markdown("### Select exogenes variables:")
    group_x = st.pills("Select exogenous variables", options=group_options, selection_mode= "multi", default = [x for x in group_options if x != group])
    pricearea_x = st.pills("Select exogenous price areas", options=pricearea_options, selection_mode="multi", default=[x for x in pricearea_options if x != pricearea])
with cols[2]:
    ci = st.toggle("Show Confidence Intervals", value=True)


# =========================================
#          FORECASTING
# =========================================

start_idx = df.index.get_loc(trainin_time[0])
end_idx = df.index.get_loc(trainin_time[1])
y_data = df.loc[:, (group, pricearea)]
x_data = df.loc[:, (group_x, pricearea_x)]
st.markdown("---")


imputer = SimpleImputer(strategy='mean') 
x_data[:] = imputer.fit_transform(x_data) #impute to handle missing values

predict_dy, predict_dy_ci, forecast = sarimax_forecast(x_data, y_data, start_idx, end_idx,
                                                       *params, *season_params) #forecast

#metrics
st.markdown(f'**MEAN Squared Error:** {mean_squared_error(y_data.iloc[end_idx:].values, forecast.values):.2f} ')
st.markdown(f'**R2 Score:** {r2_score(y_data.iloc[end_idx:].values, forecast.values):.2f} ')

st.markdown("---")

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
    st.markdown(f'Elhub API https://api.elhub.no')

