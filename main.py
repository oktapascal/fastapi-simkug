from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {'status': 'OK', 'message': 'Hello From Fastapi-YPTKUG'}