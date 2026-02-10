from fastapi import FastAPI

app = FastAPI()

print("App is working fine")

@app.get("/")
def read_root():
    return {"status": "ok"}


