import streamlit as st
import pandas as pd
from utilities import get_weather,extract_coordinates
import plotly.graph_objects as go
import numpy as np
from scipy.fftpack import dct, idct

@st.cache_data(ttl=600)
def high_pass(df : pd.DataFrame, cutoff : int = 50,nstd : float = 2.0):

    temp = df["temperature_2m"].to_numpy()
    fourier = dct(temp, norm="forward")
    
    if len(fourier) == 0:
        st.error("Fourier data is empty.")
        return None
    if df.empty:
        st.error("DataFrame is empty.")
        return None
    #Plot the temperature as a function of time
    satv = fourier.copy()
    satv[:cutoff] = 0 #high pass filter
    satv_reconstructed = idct(satv, norm="forward")
    mean,std = satv_reconstructed.mean(), satv_reconstructed.std()    

    outliers = np.where((satv_reconstructed > mean + nstd*std) | (satv_reconstructed < mean - nstd*std))
    df_outliers = df.iloc[outliers]

    low_pass = fourier.copy()
    low_pass[cutoff:] = 0 #low pass filter
    low_pass_reconstructed = idct(low_pass, norm="forward")

    st.write(f"low_pass_reconstructed lengde: {len(low_pass_reconstructed)}")
    st.write(f"low_pass_reconstructed min/max: {low_pass_reconstructed.min():.2f} / {low_pass_reconstructed.max():.2f}")
    st.write(f"low_pass_reconstructed mean: {low_pass_reconstructed.mean():.2f}")
    st.write(f"low_pass_reconstructed std: {low_pass_reconstructed.std():.2f}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["temperature_2m"], mode='lines', name='Original'))
    fig.add_trace(go.Scatter(x=df.index, y=low_pass_reconstructed + nstd*std, mode='lines', name='Upper boundary', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df.index, y=low_pass_reconstructed - nstd*std, mode='lines', name='Lower boundary', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df_outliers.index, y=df_outliers["temperature_2m"], mode='markers', name='Outliers', marker=dict(color='red')))
    #fig.add_trace(go.Scatter(x=df.index, y=satv_reconstructed, mode='lines', name='High-pass Filtered', line=dict(color='green')))
    fig.update_layout(title='Temperature Data with lower and upper boundaries',
                      xaxis_title='Time',
                      yaxis_title='Temperature (°C)')
    return fig

st.set_page_config(layout="wide")
st.title("Outlier Detection and LOF analysis")

# =================================
#           DATA LOADING
# =================================
lat,lon = extract_coordinates("Bergen")
data = get_weather(lat, lon, 2019)
df = pd.DataFrame(data.get("hourly"))
df["time"] = pd.to_datetime(df["time"])
df.set_index("time", inplace=True)

if "price_area" not in st.session_state:
    st.session_state['price_area'] = "NO2"




#===========================================
#   OUTLIER DETECTION AND LOF ANALYSIS
#===========================================
tabs = st.tabs(["Outlier Detection", "LOF Analysis"])

with tabs[0]:
    st.subheader("Outlier Detection")
    spc_selection = st.columns(2)
    with spc_selection[0]:
        cutoff = st.slider("Cutoff frequency for high-pass filter", min_value=1, max_value=200, value=50, step=1)
    with spc_selection[1]:
        nstd = st.slider("Number of standard deviations for boundary", min_value=0.5, max_value=5.0, value=2.0, step=0.1)

    

    fig = high_pass(df = df , cutoff=cutoff,nstd=nstd)
    st.plotly_chart(fig)
