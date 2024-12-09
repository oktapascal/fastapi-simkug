from http.cookiejar import month

from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, BackgroundTasks, File, Query
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from database import database
from datetime import datetime as dt, datetime
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

@app.post('/api/calculate-bond')
def calculate_bond(rate_coupon: float = Form(), rate_yield: float = Form(), frequency_count: int = Form(), nominal: float = Form(), issue_date: str = Form(), maturity_date: str = Form()):
  try:
    coupon_rate =  rate_coupon/100
    yield_rate =  rate_yield/100
    frequency = frequency_count
    nominal = nominal * 1e9

    # Assume today's date as the issue date for simplicity
    issue_date = datetime.strptime(issue_date, "%Y-%m-%d")
    maturity_date = datetime.strptime(maturity_date, "%Y-%m-%d")

    # Calculate time to each cash flow (in years)
    number_periods = frequency * ((maturity_date.year - issue_date.year) + (maturity_date.month - issue_date.month) / 12)
    cashflow_dates = []
    for i in range (1, int(number_periods) + 1):
      cashflow_dates.append(issue_date + pd.DateOffset(months=int(12/frequency*i)))

    cashflow_times = []
    for i in cashflow_dates:
      cashflow_times.append((i-issue_date).days/365.0)

    # Calculate cash flows
    cash_flows = [nominal * coupon_rate/frequency] * (len(cashflow_times) - 1) + [nominal * (1+coupon_rate/frequency)]

    # Discount cash flows to present value
    discount_factors = []
    for i in cashflow_times:
      discount_factors.append(1/(1+yield_rate/frequency) ** (frequency * i))

    pv_cash_flows = []
    for cf, df in zip(cash_flows, discount_factors):
      pv_cash_flows.append(cf * df)

    # Calculate Macaulay Duration
    maculay_duration = sum(ct * pcf for ct, pcf in zip(cashflow_times, pv_cash_flows)) / sum(pv_cash_flows)

    # Calculate Modified Duration
    modified_duration = maculay_duration / (1+yield_rate/frequency)

    return {'status': 'OK', 'maculay_duration': maculay_duration, 'modified_duration': modified_duration }
  except Exception as ex:
    return {'status': 'ERROR', 'message': str(ex)}

