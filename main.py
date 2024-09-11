from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from database import database
import os

load_dotenv()

def connect_dbproduk():
    engine = database.Database(os.getenv('DB_USER1'), os.getenv('DB_PASSWORD1'), os.getenv('DB_HOST1'),
                               os.getenv('DB_NAME1'))

    return engine.connect()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"]
)

@app.get("/")
def root():
    return {'status': 'OK', 'message': 'Hello From Fastapi-YPTKUG'}

@app.get('/test-db')
def test_db():
    try:
        dbproduk = connect_dbproduk()
        print("{c} is working".format(c=dbproduk))
        dbproduk.close()

        return {'status': 'OK', 'message': 'Success Connect Database'}
    except pyodbc.Error as ex:
        print("{c} is not working".format(c=dbproduk))