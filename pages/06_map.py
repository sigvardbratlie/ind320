import streamlit as st
import pandas as pd
import folium
import json
from streamlit_folium import st_folium
import os
from utilities import init, sidebar_setup,get_elhub_data,init_connection,el_sidebar
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

st.set_page_config(
    page_title="Map Selection",
    page_icon="🗺️",
)
st.title("🗺️ Map Selection of Price Areas 🔋⚡️")

init()
init_connection()
sidebar_setup("map")
el_sidebar()

df = get_elhub_data(st.session_state["client"],dataset=st.session_state.dataset,dates = st.session_state.dates,)
dfg = df.groupby("pricearea")["quantitykwh"].mean().reset_index()
norm = Normalize(vmin=dfg["quantitykwh"].min(), vmax=dfg["quantitykwh"].max())
colormap = plt.cm.Blues  # eller RdYlGn, Viridis osv

def get_color(value):
    rgba = colormap(norm(value))
    return '#{:02x}{:02x}{:02x}'.format(int(rgba[0]*255), int(rgba[1]*255), int(rgba[2]*255))

def load_map():
    #load file and error handling
    try:
        with open("data/file.geojson") as f:
            gj = json.load(f)
    except FileNotFoundError:
        st.error("GeoJSON file not found.")
        return None
    except Exception as e:
        st.error(f"An error occurred while loading the GeoJSON file: {e}")
        return None
    
    for feature in gj.get("features", []):
        label = feature.get("properties", {}).get('ElSpotOmr','').replace(" ","")
        feature.get("properties", {})['ElSpotOmr'] = label
        kwh = dfg.loc[dfg['pricearea'] == label, 'quantitykwh'].values
        if len(kwh) > 0:
            feature['properties']['quantitykwh'] = float(kwh[0])
        else:
            feature['properties']['quantitykwh'] = 0.0

    
    m = folium.Map(location=[59.911491, 10.757933], zoom_start=4,tiles='CartoDB positron') #create map

    folium.Choropleth(
                geo_data=gj,
                name='Production',
                data=dfg,
                columns=['pricearea', 'quantitykwh'],
                key_on='feature.properties.ElSpotOmr',
                fill_color='Blues',
                fill_opacity=0.7,
                line_opacity=0.2,
                line_color='black',
                legend_name='Average kWh',
                popup=folium.features.GeoJsonPopup(
                    fields=['ElSpotOmr', 'quantitykwh'],
                    aliases=['Price Area', 'kWh']
                )
            ).add_to(m)
    
    folium.GeoJson(
                gj,
                tooltip=folium.features.GeoJsonTooltip(
                    fields=['ElSpotOmr', 'quantitykwh'],
                    aliases=['Price Area', 'kWh'])
            ).add_to(m)
    
    folium.LayerControl().add_to(m)
    return m

m = load_map()

def callback():
    try:
        prop = st.session_state.get("my_map",{}).get("last_active_drawing",{}).get("properties",{})
        if prop:
            st.session_state.price_area = prop.get("ElSpotOmr","NO2").replace(" ","")
        else:
            st.session_state.price_area = "NO2"
    except (AttributeError, TypeError) as e:
        st.session_state.price_area = "NO2"
    except Exception as e:
        st.error(f"Error in callback: {e}")

st_folium(m,width = "100%",height=600,
          on_change=callback,
          key="my_map")

