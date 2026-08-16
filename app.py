import streamlit as st

st.set_page_config(page_title="Streamlit App", page_icon="🎈")

print("App is working fine")

st.json({"status": "new"})