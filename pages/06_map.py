import streamlit as st
import pandas as pd
import folium
import json
from streamlit_folium import st_folium
import os
from utilities import init, sidebar_setup

st.set_page_config(
    page_title="Map Selection",
    page_icon="🗺️",
)

init()
sidebar_setup("map")

def load_map():
    try:
        with open("data/file.geojson") as f:
            gj = json.load(f)
    except FileNotFoundError:
        st.error("GeoJSON file not found.")
        return None
    except Exception as e:
        st.error(f"An error occurred while loading the GeoJSON file: {e}")
        return None
    m = folium.Map(location=[59.911491, 10.757933], zoom_start=6,tiles='CartoDB positron')
    for feature in gj.get("features"):
        label = feature.get("properties", {}).get('ElSpotOmr')
        folium.GeoJson(
            feature,
            name=label,
            tooltip=label,
            style_function=lambda x: {
                'fillColor': 'lightblue',
                'color': 'black',
                'weight': 2,
                'fillOpacity': 0.3
                },
            highlight_function=lambda x: {
                'fillColor': 'orange',
                'color': 'red',
                'weight': 3,
                'fillOpacity': 0.7
            }
        ).add_to(m)

    return m

m = load_map()
#st.json(st.session_state)

def callback():
    if "my_map" in st.session_state and "last_active_drawing" in st.session_state["my_map"] and "properties" in st.session_state["my_map"]["last_active_drawing"]:
        st.session_state.price_area = (st.session_state.get('my_map', {})
                                    .get("last_active_drawing", {})
                                    .get("properties", {}).get("ElSpotOmr").replace(" ",""))
    else:
        st.session_state.price_area = "NO2"
st_folium(m,width = "100%",height=600,
          on_change=callback,
          key="my_map")

# st.info("Price area {}".format(st.session_state.get("price_area","Not selected")))
# st.info("Start date: {}".format(st.session_state.get("start_date","Not selected")))
# st.info("End date: {}".format(st.session_state.get("end_date","Not selected")))

