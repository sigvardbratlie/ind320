import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from utilities import init, sidebar_setup,get_elhub_data,init_connection,el_sidebar,get_weather_data,extract_coordinates
from plotly import subplots
import plotly.graph_objects as go

# =========================================
#          FUNCTION DEFINITIONS & SETUP
# =========================================
st.set_page_config(
    page_title="Map Selection",
    page_icon="🗺️",
)
st.title("Correlation between Meteorology and Energy Production")

init()
init_connection()
sidebar_setup("map")
el_sidebar()


# =========================================
#          LOAD DATA
# =========================================
coordinates = st.session_state.get("location",{}).get("coordinates", None)
city = st.session_state.get("location",{}).get("city", None)
price_area = st.session_state.get("location",{}).get("price_area", "NO1")

#st.json(st.session_state)
df_el = get_elhub_data(st.session_state["client"],
                       dataset=st.session_state.group.get("name"),
                       dates = st.session_state.dates,
                       filter_group=True,
                       aggregate_group=True)


df_w = get_weather_data(coordinates=coordinates, dates = st.session_state.dates, set_time_index=True)


cols = st.columns(2)
with cols[0]:
    weather_col = st.selectbox("Select weather variable", options=df_w.columns.tolist(), index=1)
    df_w = df_w[[weather_col]]
with cols[1]:
    el_col = st.selectbox("Select electricity variable", options=df_el.columns.tolist(), index=0)


df_merged = pd.merge_asof(df_el.sort_index(), df_w.sort_index(), 
                          left_index=True, right_index=True, 
                          direction="nearest", )

# =========================================
#                   CALCULATE
# =========================================

lag = st.slider("Select lag (hours)", min_value=0, max_value=10000, value=0, step=10)
time = st.select_slider("Select time", options=df_merged.index.tolist(), value=df_merged.index[len(df_merged)//2])
window = st.slider("Window length (days)", min_value=1, max_value=365, value=30, step=1)*24

rolling_corr = df_merged[el_col].shift(lag).rolling(window, center=True).corr(df_merged[weather_col])


center_idx = df_merged.index.get_loc(time)
half_window = window // 2
start_idx = max(0, center_idx - half_window)
end_idx = min(len(df_merged), center_idx + half_window)

fig = subplots.make_subplots(rows=3, cols=1, shared_xaxes=True)

# =================================
#           PLOTTING
# =================================

fig.add_trace(go.Scatter(x=df_merged.index, y=df_merged[el_col], 
                         name=el_col, line=dict(color='lightgray')), row=1, col=1)
fig.add_trace(go.Scatter(x=df_merged.index[start_idx+lag:end_idx+lag], 
                         y=df_merged[el_col].iloc[start_idx+lag:end_idx+lag], 
                         name=f'{el_col} shifted (used)', 
                         line=dict(color='red', width=3)), row=1, col=1)

fig.add_trace(go.Scatter(x=df_merged.index, y=df_merged[weather_col], 
                         name=weather_col, line=dict(color='lightgray')), row=2, col=1)
fig.add_trace(go.Scatter(x=df_merged.index[start_idx:end_idx], 
                         y=df_merged[weather_col].iloc[start_idx:end_idx], 
                         name=f'{weather_col} (used)', 
                         line=dict(color='blue', width=3)), row=2, col=1)

# Plot 3: Rolling correlation
fig.add_trace(go.Scatter(x=rolling_corr.index, y=rolling_corr, 
                         name=f'Correlation (lag={lag}h)'), row=3, col=1)
fig.add_vline(x=df_merged.index[center_idx], line_dash="dash", line_color="green", row=3, col=1)

fig.update_yaxes(title_text=el_col, row=1, col=1)
fig.update_yaxes(title_text=weather_col, row=2, col=1)
fig.update_yaxes(title_text="Correlation", row=3, col=1)
st.plotly_chart(fig)

