"""
STL Decomposition and Spectrogram Analysis Page

Provides tools for analyzing electricity data using STL decomposition and spectrograms.
Users can adjust parameters like seasonal period, smoothers, window length, and overlap.
"""
import streamlit as st
import pandas as pd
import numpy as np
from scipy import signal
from statsmodels.tsa.seasonal import STL
from typing import Literal
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utilities import get_elhub_data, init, check_mongodb_connection, el_sidebar, sidebar_setup

# =========================================
#          FUNCTION DEFINITIONS & SETUP
# =========================================
@st.cache_data(ttl=3600)
def loess(
    data: pd.DataFrame,
    price_area: Literal["NO1", "NO2", "NO3", "NO4", "NO5"] = "NO2",
    production_group: Literal["hydro", "wind", "solar", "thermal"] = "hydro",
    period: int = 24 * 7,
    seasonal_smoother: int = 141,
    trend_smoother: int = 141,
    robust: bool = True,
) -> go.Figure:
    """
    Perform STL decomposition on electricity production data.

    Args:
        data: DataFrame containing electricity production data.
        price_area: Norwegian price area to analyze.
        production_group: Type of energy production to analyze.
        period: Seasonal period in hours.
        seasonal_smoother: Length of seasonal smoothing window (must be odd).
        trend_smoother: Length of trend smoothing window (must be odd).
        robust: Whether to use robust STL.

    Returns:
        Plotly figure with decomposition plots (Observed, Trend, Seasonal, Residual).
    """
    if data.empty:
        st.warning("No data available.")
        return go.Figure()

    if period > trend_smoother:
        trend_smoother = period + 1 if period % 2 == 0 else period

    data_filtered = data.loc[(data["pricearea"] == price_area) & (data["productiongroup"] == production_group), "quantitykwh"]
    if data_filtered.empty:
        st.warning(f"No data available for Area: {price_area}, Group: {production_group}")
        return go.Figure()

    stl = STL(data_filtered, 
            period = period,
            robust=robust, 
            seasonal=seasonal_smoother, 
            trend=trend_smoother,
            )

    res = stl.fit() 

    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                        subplot_titles=("Observed", "Trend", "Seasonal", "Residual"))

    fig.add_trace(go.Scatter(x=res.observed.index, y=res.observed, name="Observed"), row=1, col=1)
    fig.add_trace(go.Scatter(x=res.trend.index, y=res.trend, name="Trend"), row=2, col=1)
    fig.add_trace(go.Scatter(x=res.seasonal.index, y=res.seasonal, name="Seasonal"), row=3, col=1)
    fig.add_trace(go.Scatter(x=res.resid.index, y=res.resid, name="Residual"), row=4, col=1)
    fig.update_layout(height=800, width=1400, 
                        )
    #                 title_text = f"STL Decomposition. Area: {price_area}, Group: {production_group}, Period: {period}"
    #                 
                    
    return fig

@st.cache_data(ttl=7200)
def spectrogram(
    data: pd.DataFrame,
    price_area: Literal["NO1", "NO2", "NO3", "NO4", "NO5"] = "NO2",
    production_group: Literal["hydro", "wind", "solar", "thermal"] = "hydro",
    window_length: int = 256,
    overlap: int = 128,
) -> go.Figure:
    """
    Generate a spectrogram of electricity production data.

    Args:
        data: DataFrame containing electricity production data.
        price_area: Norwegian price area to analyze.
        production_group: Type of energy production to analyze.
        window_length: Length of FFT window.
        overlap: Number of overlapping samples between windows.

    Returns:
        Plotly heatmap figure showing the spectrogram.
    """

    data = data.loc[(data["pricearea"] == price_area) & (data["productiongroup"] == production_group), "quantitykwh"]
    if data.empty:
        st.warning(f"No data available for Area: {price_area}, Group: {production_group}")
        return go.Figure()

    fs = 1.0 #sampling frequency for hourly data
    f, t, Sxx = signal.spectrogram(data.to_numpy(), 
                                   fs,
                                   nperseg=window_length,
                                   noverlap=overlap,)

    fig = go.Figure(data=go.Heatmap(
        z=10 * np.log10(Sxx),  # convert to dB scale
        x=t,
        y=f,
        colorscale='Viridis'
    ))

    fig.update_layout(
        width = 1400,
        height = 600,
        #title='Spectrogram of Production Data. Area: ' + price_area + ', Group: ' + production_group,
        xaxis_title='Time',
        yaxis_title='Frequency'
    )
    return fig

init()
st.set_page_config(layout="wide")
st.title("STL Decomposition and Spectrogram 🔋⚡️")
# =================================
#           DATA LOADING
# =================================
sidebar_setup()
el_sidebar(radio_group=True)

coordinates = st.session_state.get("location",{}).get("coordinates", None)
city = st.session_state.get("location",{}).get("city", None)
price_area = st.session_state.get("location",{}).get("price_area", "NO1")

data = get_elhub_data(st.session_state["client"], dataset=st.session_state.group.get("name"),dates = st.session_state.dates,filter_group=False,aggregate_group=False) 


#===========================================
#   STL DECOMPOSITION AND SPECTROGRAM
#===========================================
tabs = st.tabs(["STL", "Spectrogram"])

with tabs[0]:
    st.subheader("STL Decomposition")
    stl_selection_cols = st.columns(4)
    with stl_selection_cols[0]:
        period = st.select_slider(
            "Select Seasonal Period",
            options=[24, 24*7, 24*30, 24*365],
            value=24*7,
        ) #widget for selecting seasonal period
    
    with stl_selection_cols[1]:
        seasonal_smoother = st.select_slider(
            "Select Seasonal Smoother",
            options=[13, 25, 51, 101, 141, 201],
            value=141,
        ) #widget for selecting seasonal smoother

    with stl_selection_cols[2]:
        trend_smoother = st.select_slider(
            "Select Trend Smoother",
            options=[13, 25, 51, 101, 141, 201],
            value=141,
        ) #widget for selecting trend smoother
    
    with stl_selection_cols[3]:
        robust = st.checkbox("Robust STL", value=True)

    if isinstance(st.session_state.group.get("values"), list):
        group = st.session_state.group.get("values")[0]  #select first group if multiple selected
    else:
        group = st.session_state.group.get("values")
    
#===========================================
#           STL DECOMPOSITION
#===========================================
    fig = loess(data = data,
                period = period,
        production_group=group,
        price_area=price_area,
        robust=robust) #Weekly seasonality for wind
    st.plotly_chart(fig, key = "stl_plot")

with tabs[1]:
    st.subheader("Spectrogram")

    spect_selections = st.columns(2)
    with spect_selections[0]:
        window_length = st.select_slider(
            "Select Window Length",
            options=[128, 256, 512, 1024],
            value=256,
        ) #widget for selecting window length
    with spect_selections[1]:
        overlap = st.select_slider(
            "Select Overlap",
            options=[64, 128, 256, 512],
            value=128,
        ) #widget for selecting overlap

#===========================================
#           SPECTROGRAM
#===========================================
    fig = spectrogram(data = data, 
                      production_group=group, 
                      price_area=price_area,
                      window_length=window_length,
                      overlap=overlap)
    st.plotly_chart(fig, key = "spectrogram_plot")

with st.expander("Data sources"):
    st.write(f'Elhub API https://api.elhub.no')
