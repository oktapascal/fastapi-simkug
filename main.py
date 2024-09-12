from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, BackgroundTasks, File, Query
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from database import database
from datetime import datetime as dt
import os
import time
import platform
import psutil
import pyodbc
import pandas as pd
import math

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

@app.get('/')
def root():
  return {'status': 'OK', 'message': 'Hello From Fastapi-YPTKUG'}

@app.get('/test-db')
def test_db():
  try:
    dbproduk = connect_dbproduk()
    print('{c} is working'.format(c=dbproduk))
    dbproduk.close()

    return {'status': 'OK', 'message': 'Success Connect Database'}
  except pyodbc.Error as ex:
    print('{c} is not working'.format(c=dbproduk))


@app.get('/api/excel/export/buku-besar')
def excel_export_bukubesar(background_task: BackgroundTasks):
  try:
    columns = ['NO BUKTI','NO DOKUMEN','TANGGAL','KODE PP','KETERANGAN','DEBET','KREDIT']

    t0 = time.perf_counter()

    dbproduk = connect_dbproduk()
    cursor = dbproduk.cursor()

    query = f'''
    select a.no_bukti,a.no_dokumen,a.tanggal,a.kode_pp,a.keterangan,
      case when a.dc='D' then a.nilai else 0 end as debet,case when a.dc='C' then a.nilai else 0 end as kredit
    from gldt a
    where a.kode_lokasi=? and a.kode_akun=? and a.periode=?
    order by a.tanggal
    '''
    params = ['51','1152007','202301']
    cursor.execute(query, params)

    read_time = f'{time.perf_counter() - t0:.1f} seconds'

    df = pd.DataFrame.from_records(cursor.fetchall(), columns=columns)

    today = dt.now()
    unique_id = today.strftime('%Y%m%d%H%M%S')

    file_name = f'DATA_GL_{unique_id}.xlsx'

    writer = pd.ExcelWriter(file_name)
    df.to_excel(writer, index=False)

    writer.close()
    cursor.close()
    dbproduk.close()

    execution_time = f'{time.perf_counter() - t0:.1f} seconds'

    headerResponse = {
      'Content-Disposition': 'attachment; filename="' + file_name + '"'
    }

    background_task.add_task(os.remove, file_name)

    os_info = platform.system()
    total_memory = psutil.virtual_memory().total / (1024 ** 3)
    used_memory = psutil.virtual_memory().used / (1024 ** 3)
    total_memory_rounded = math.ceil(total_memory * 100) / 100
    used_memory_rounded = math.ceil(used_memory * 100) / 100
    total_cpu = psutil.cpu_count()
    cpu_usage = psutil.cpu_percent(interval=1)

    print('='*48)
    print(f'OS: {os_info}')
    print(f'CPU: {total_cpu} cores')
    print(f'CPU Usage: {cpu_usage}%')
    print(f'RAM: {total_memory_rounded} GB')
    print(f'RAM Usage: {used_memory_rounded} GB')
    print(f'DB Read Time: {read_time}')
    print(f'Execution Time: {execution_time}')
    print('='*48)

    return FileResponse(path=file_name, headers=headerResponse, filename=file_name)
  except Exception as ex:
    return {'status': 'ERROR', 'message': str(ex)}
