import streamlit as st
import pandas as pd
from utilities import get_weather_data,extract_coordinates,init,sidebar_setup
import plotly.graph_objects as go
import numpy as np
from scipy.fft import dct, idct
from sklearn.neighbors import LocalOutlierFactor
<<<<<<< HEAD:pages/05_ New B.py
from scipy.stats import median_abs_deviation
=======
from scipy.stats import median_abs_deviation,trim_mean
>>>>>>> ca4:pages/05_🌡️☁️ Outliers & LOF.py

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
    norm = None
    fourier = dct(data, norm=norm)
    #Plot the temperature as a function of time
    satv = fourier.copy()
    f = np.arange(0, len(satv))
    satv[f<cutoff] = 0 #high pass filter
    return idct(satv, norm=norm)

@st.cache_data(ttl=600)
def high_pass(df : pd.DataFrame,feature : str,cutoff : int = 50 , nstd : float = 2.0):

    temp = df[feature].to_numpy()    
    if df.empty:
        st.error("DataFrame is empty.")
        return None
    satv_reconstructed = calc_highpass(temp, cutoff)
<<<<<<< HEAD:pages/05_ New B.py
    #mean,std = satv_reconstructed.mean(), satv_reconstructed.std()    
    MAD = median_abs_deviation(satv_reconstructed)
    std = 1.4826 * MAD

    outliers = np.where((satv_reconstructed > MAD + nstd*std) | (satv_reconstructed < MAD - nstd*std))
=======
    MAD = median_abs_deviation(satv_reconstructed)
    std_robust = 1.4826 * MAD

    outliers = np.where((satv_reconstructed > MAD + nstd*std_robust) | (satv_reconstructed < MAD - nstd*std_robust))
>>>>>>> ca4:pages/05_🌡️☁️ Outliers & LOF.py
    n_outliers = len(outliers[0])
    df_outliers = df.iloc[outliers]

    low_pass_reconstructed = temp - satv_reconstructed
    st.info(f"Number of outliers detected: {n_outliers}")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df[feature], mode='lines', name='Original'))
    fig.add_trace(go.Scatter(x=df.index, y=low_pass_reconstructed + nstd*std_robust, mode='lines', name='Upper boundary', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df.index, y=low_pass_reconstructed - nstd*std_robust, mode='lines', name='Lower boundary', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df_outliers.index, y=df_outliers[feature], mode='markers', name='Outliers', marker=dict(color='red')))
    fig.update_layout(title='Temperature Data with lower and upper boundaries',
                      xaxis_title='Time',
                      yaxis_title='Temperature (°C)')
    return fig

init() #init default states and connections
st.set_page_config(layout="wide")
st.title("Outlier Detection and LOF analysis 🌡️☁️")
sidebar_setup("weather data analysis")

coordinates = st.session_state.get("location",{}).get("coordinates", None)
city = st.session_state.get("location",{}).get("city", None)
price_area = st.session_state.get("location",{}).get("price_area", "NO1")

# =================================
#           DATA LOADING
# =================================

df = get_weather_data(coordinates=coordinates, dates = st.session_state.dates, set_time_index=True)

#===========================================
#   OUTLIER DETECTION AND LOF ANALYSIS
#===========================================
tabs = st.tabs(["Outlier Detection", "LOF Analysis"])  #create tabs

with tabs[0]:
    col = st.radio(
            "Select feature",
            options = df.columns.tolist(),
            index = df.columns.tolist().index("temperature_2m"),
            horizontal=True,
            label_visibility="collapsed",
            )
    st.subheader("Outlier Detection")
    spc_selection = st.columns(2) #selections for outlier detection
    with spc_selection[0]:
        cutoff = st.slider("Cutoff frequency for high-pass filter", min_value=1, max_value=200, value=50, step=1)
    with spc_selection[1]:
        nstd = st.slider("Number of standard deviations for boundary", min_value=0.5, max_value=5.0, value=2.0, step=0.1)

    fig = high_pass(df = df, feature = col, cutoff=cutoff,nstd=nstd)
    st.plotly_chart(fig)

with tabs[1]:
    col = st.radio(
            "Select feature",
            options = df.columns.tolist(),
            index = df.columns.tolist().index("precipitation"),
            horizontal=True,
            label_visibility="collapsed",
            )
    
    st.subheader("LOF Analysis")
    
    lof_select = st.columns(2) #selections for LOF
    with lof_select[0]:
        n_neighbors = st.slider("Number of neighbors", min_value=1, max_value=100, value=20, step=1)
    with lof_select[1]:
        contamination = st.slider("Contamination", min_value=0.01, max_value=0.1, value=0.01, step=0.01)

    
    
    
    fig = lof(df = df , feature = col, n_neighbors=n_neighbors, contamination=contamination)
    st.plotly_chart(fig)
