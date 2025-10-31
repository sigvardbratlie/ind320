import streamlit as st
import pandas as pd
from utilities import get_weather,extract_coordinates,init
import plotly.graph_objects as go
import numpy as np
from scipy.fft import dct, idct
from sklearn.neighbors import LocalOutlierFactor

# =========================================
#          DEFINE FUNCTIONS & SETUP
# =========================================
@st.cache_data(ttl=600)
def lof(df,feature,n_neighbors: int = 20, contamination: float = 0.01):
    lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    data = df[[feature]]
    labels = lof.fit_predict(data)
    outliers = data[labels == -1]
    inliers = data[labels == 1]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=outliers.index, y=outliers[feature], mode='markers',
                             name='Outliers'))
    fig.add_trace(go.Scatter(x=inliers.index, y=inliers[feature], mode='markers',
                             name='Inliers'))
    fig.update_layout(title='',
                      xaxis_title='Time',
                      yaxis_title='Precipitation')
    return fig

def calc_highpass(data, cutoff: int):
    fourier = dct(data, norm="forward")
    #Plot the temperature as a function of time
    satv = fourier.copy()
    f = np.arange(0, len(satv))
    satv[f<cutoff] = 0 #high pass filter
    return idct(satv, norm="forward")

def calc_lowpass(data, cutoff: int):
    fourier = dct(data, norm="forward")
    #Plot the temperature as a function of time
    low_pass = fourier.copy()
    low_pass[cutoff:] = 0 #low pass filter
    return idct(low_pass, norm="forward")

@st.cache_data(ttl=600)
def high_pass(df : pd.DataFrame,feature : str,cutoff : int = 50 , nstd : float = 2.0):

    temp = df[feature].to_numpy()    
    if df.empty:
        st.error("DataFrame is empty.")
        return None
    satv_reconstructed = calc_highpass(temp, cutoff)
    mean,std = satv_reconstructed.mean(), satv_reconstructed.std()    

    outliers = np.where((satv_reconstructed > mean + nstd*std) | (satv_reconstructed < mean - nstd*std))
    df_outliers = df.iloc[outliers]

    low_pass_reconstructed = calc_lowpass(temp, cutoff)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df[feature], mode='lines', name='Original'))
    fig.add_trace(go.Scatter(x=df.index, y=low_pass_reconstructed + nstd*std, mode='lines', name='Upper boundary', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df.index, y=low_pass_reconstructed - nstd*std, mode='lines', name='Lower boundary', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df_outliers.index, y=df_outliers[feature], mode='markers', name='Outliers', marker=dict(color='red')))
    fig.update_layout(title='Temperature Data with lower and upper boundaries',
                      xaxis_title='Time',
                      yaxis_title='Temperature (°C)')
    return fig

init() #init default states and connections
st.set_page_config(layout="wide")
st.title("Outlier Detection and LOF analysis 🌡️☁️")
with st.sidebar:
    st.info("Weather data")

# =================================
#           DATA LOADING
# =================================
lat,lon = extract_coordinates("Bergen")
data = get_weather(lat, lon, 2019)
df = pd.DataFrame(data.get("hourly"))
df["time"] = pd.to_datetime(df["time"])
df.set_index("time", inplace=True)

 

col = st.radio(
    "Select feature",
    options = df.columns.tolist(),
    index = df.columns.tolist().index("temperature_2m"),
    horizontal=True,
    label_visibility="collapsed",
    )


#===========================================
#   OUTLIER DETECTION AND LOF ANALYSIS
#===========================================
tabs = st.tabs(["Outlier Detection", "LOF Analysis"])  #create tabs

with tabs[0]:
    st.subheader("Outlier Detection")
    spc_selection = st.columns(2) #selections for outlier detection
    with spc_selection[0]:
        cutoff = st.slider("Cutoff frequency for high-pass filter", min_value=1, max_value=200, value=50, step=1)
    with spc_selection[1]:
        nstd = st.slider("Number of standard deviations for boundary", min_value=0.5, max_value=5.0, value=2.0, step=0.1)

    fig = high_pass(df = df, feature = col, cutoff=cutoff,nstd=nstd)
    st.plotly_chart(fig)

with tabs[1]:
    st.subheader("LOF Analysis")
    
    lof_select = st.columns(2) #selections for LOF
    with lof_select[0]:
        n_neighbors = st.slider("Number of neighbors", min_value=1, max_value=100, value=20, step=1)
    with lof_select[1]:
        contamination = st.slider("Contamination", min_value=0.01, max_value=0.1, value=0.01, step=0.01)
    
    fig = lof(df = df , feature = col, n_neighbors=n_neighbors, contamination=contamination)
    st.plotly_chart(fig)
