import streamlit as st
import pandas as pd
import folium
import json
from streamlit_folium import st_folium
import os
from utilities import init, sidebar_setup,get_elhub_data,init_connection,el_sidebar,get_weather_data,extract_coordinates
from Snow_drift import snowdrift
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

@st.cache_data(ttl=600)
def load_geodata(dfg : pd.DataFrame):
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
        kwh = dfg.loc[dfg['pricearea'] == label, 'quantitymwh'].values
        if len(kwh) > 0:
            feature['properties']['quantitymwh'] = float(kwh[0])
        else:
            feature['properties']['quantitymwh'] = 0.0

    return gj
    


st.set_page_config(
    page_title="Map Selection",
    page_icon="🗺️",
)
st.title("🗺️ Map Selection of Price Areas 🔋⚡️")

init()
init_connection()
sidebar_setup("map")
el_sidebar()


coordinates = st.session_state.get("location",{}).get("coordinates", None)
city = st.session_state.get("location",{}).get("city", None)
price_area = st.session_state.get("location",{}).get("price_area", "NO1")

df_el = get_elhub_data(st.session_state["client"],dataset=st.session_state.dataset,dates = st.session_state.dates,)
#st.info("Dataset: " + st.session_state.dataset)
#st.info(f"Production Groups: {st.session_state.production_group}" if st.session_state.dataset == "production" else f"Consumption Groups: {st.session_state.consumption_group}")
if st.session_state.dataset == "production":
    df_el = df_el[df_el["productiongroup"].isin(st.session_state.production_group)]
elif st.session_state.dataset == "consumption":
    df_el = df_el[df_el["consumptiongroup"].isin(st.session_state.consumption_group)]   

dfg = df_el.groupby("pricearea")["quantitykwh"].mean().reset_index()
dfg["quantitymwh"] = dfg["quantitykwh"] // 1e3  # Convert to kWh
norm = Normalize(vmin=dfg["quantitymwh"].min(), vmax=dfg["quantitymwh"].max())
colormap = plt.cm.Blues  # eller RdYlGn, Viridis osv

#st.dataframe(df_el.head())
#st.dataframe(df_el["consumptiongroup"].value_counts())
#st.info(df_el["consumptiongroup"].unique())


gj = load_geodata(dfg = dfg)


weather_data = get_weather_data(lat = coordinates[0], lon = coordinates[1], dates = st.session_state.dates)
df_w = pd.DataFrame(weather_data.get("hourly"))
df_w["time"] = pd.to_datetime(df_w["time"])

def get_color(value):
    rgba = colormap(norm(value))
    return '#{:02x}{:02x}{:02x}'.format(int(rgba[0]*255), int(rgba[1]*255), int(rgba[2]*255))

def load_map(gj,coordinates : tuple = None):
    if coordinates:
        start_coordinates = list(coordinates)
    else:
        start_coordinates = [59.911491, 10.757933]  # Default to Oslo

    
    m = folium.Map(location=start_coordinates, zoom_start=4,tiles='CartoDB positron') #create map

    folium.Choropleth(
                geo_data=gj,
                name='Production',
                data=dfg,
                columns=['pricearea', 'quantitymwh'],
                key_on='feature.properties.ElSpotOmr',
                fill_color='Blues',
                fill_opacity=0.7,
                line_opacity=0.2,
                line_color='black',
                legend_name='Average MWh',
                popup=folium.features.GeoJsonPopup(
                    fields=['ElSpotOmr', 'quantitymwh'],
                    aliases=['Price Area', 'MWh']
                )
            ).add_to(m)
    
    folium.GeoJson(
                gj,
                tooltip=folium.features.GeoJsonTooltip(
                    fields=['ElSpotOmr', 'quantitymwh'],
                    aliases=['Price Area', 'MWh'])
            ).add_to(m)
    if coordinates:
        lat, lon = coordinates
        folium.Marker(
                location=[lat, lon],
                popup=city,
                icon=folium.Icon(color='green', icon='info-sign')
            ).add_to(m)

    folium.LayerControl().add_to(m)
    return m

m = load_map(gj, coordinates=coordinates)

def callback():
    try:
        prop = st.session_state.get("my_map",{}).get("last_active_drawing",{}).get("properties",{})
        if prop:
            st.session_state.price_area = prop.get("ElSpotOmr","").replace(" ","")
        
    except (AttributeError, TypeError) as e:
        pass
    except Exception as e:
        st.error(f"Error in callback: {e}")

st_folium(m,width = "100%",height=600,
          on_change=callback,
          key="my_map")

plot, fence_df,yearly_df, overall_avg = snowdrift(df = df_w)
st.plotly_chart(plot,use_container_width=True)
st.write("\nYearly average snow drift (Qt) per season:")
st.write(f"Overall average Qt over all seasons: {overall_avg / 1000:.1f} tonnes/m")

yearly_df_disp = yearly_df.copy()
yearly_df_disp["Qt (tonnes/m)"] = yearly_df_disp["Qt (kg/m)"] / 1000
st.write("\nYearly average snow drift (Qt) per season (in tonnes/m) and control type:")
st.dataframe(yearly_df_disp[['season', 'Qt (tonnes/m)', 'Control']].style.format({
    'Qt (tonnes/m)': "{:.1f}"
}))

overall_avg_tonnes = overall_avg / 1000
st.write(f"\nOverall average Qt over all seasons: {overall_avg_tonnes:.1f} tonnes/m")
st.write("\nNecessary fence heights per season (in meters):")
st.dataframe(fence_df.style.format({
        "Wyoming (m)": "{:.1f}",
        "Slat-and-wire (m)": "{:.1f}",
        "Solid (m)": "{:.1f}"
    }))
