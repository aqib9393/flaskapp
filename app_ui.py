import streamlit as st

st.set_page_config(page_title="ASGI Streamlit App", page_icon="⚡")

st.title("Streamlit with ASGI")
st.json({"status": "new", "architecture": "ASGI / Uvicorn"})