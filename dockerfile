FROM python:3.12-slim

# WORKDIR /main
WORKDIR /app


COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", "-b", "0.0.0.0:8000", "app:app"]