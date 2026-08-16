import os
import subprocess
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware

app = FastAPI()

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

# To execute Streamlit directly inside an ASGI lifecycle:
@app.get("/api/streamlit")
def run_streamlit_app():
    import streamlit.web.cli as stcli
    import sys
    sys.argv = ["streamlit", "run", "app_ui.py", "--server.port=8501", "--server.address=0.0.0.0"]
    stcli.main()

if __name__ == "__main__":
    run_streamlit_app()