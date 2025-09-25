import streamlit as st

st.set_page_config(layout="wide") #setting page conig with layout wide to fill the page

st.title("CA1 - Home page")
st.header("Header 1")

with st.sidebar:
    st.write("Sidebar")
