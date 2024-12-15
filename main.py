from http.cookiejar import month

from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, BackgroundTasks, File, Query
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from database import database
from datetime import datetime as dt, datetime, timedelta
import os
import time
import platform
import psutil
import pyodbc
import pandas as pd
import math
import numpy as np

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

# @app.post('/api/calculate-bond')
# def calculate_bond(rate_coupon: float = Form(), rate_yield: float = Form(), frequency_count: int = Form(), basis: int = Form(), nominal: float = Form(), issue_date: str = Form(), maturity_date: str = Form()):
#   try:
#     coupon_rate =  rate_coupon/100
#     yield_rate =  rate_yield/100
#     frequency = frequency_count
#     basis_point = basis
#     face_value = nominal * 1e9
#
#     # Assume today's date as the issue date for simplicity
#     issue_date = pd.to_datetime(issue_date, format="%Y-%m-%d")
#     maturity_date = pd.to_datetime(maturity_date, format="%Y-%m-%d")
#
#     data = pd.DataFrame()
#     n = pd.to_numeric(((pd.to_datetime(maturity_date) - pd.to_datetime(issue_date))/365).days)
#     total_payment = n * frequency
#     coupon_payment = coupon_rate / frequency * face_value
#     payment = [coupon_payment] * (total_payment-1) + [coupon_payment + face_value]
#
#     # Generate payment dates
#     payment_dates = [issue_date + pd.DateOffset(months=int(12 / frequency) * i) for i in range(1, total_payment + 1)]
#
#     # Calculate cashflow times based on basis
#     cashflow_dates = []
#     if basis_point in [0, 2, 3, 4]:
#       number_periods = frequency * (
#             (maturity_date.year - issue_date.year) + (maturity_date.month - issue_date.month) / 12)
#       cashflow_dates = [issue_date + pd.DateOffset(months=int(12 / frequency * i)) for i in
#                         range(1, int(number_periods) + 1)]
#     elif basis_point == 1:
#       current_date = issue_date
#       while current_date < maturity_date:
#         current_date += timedelta(days=int(365 / frequency))
#         if current_date > maturity_date:
#           current_date = maturity_date
#         cashflow_dates.append(current_date)
#     else:
#       return {'status': 'ERROR', 'message': 'Invalid basis'}
#
#     # Calculate time to each cash flow
#     if basis_point in [0, 4]:
#       cashflow_times = [(date - issue_date).days / 365.0 for date in cashflow_dates]
#     elif basis_point == 1:
#       cashflow_times = [(date - issue_date).days / 365.0 for date in cashflow_dates]
#     elif basis_point == 2:
#       cashflow_times = [(date - issue_date).days / 360.0 for date in cashflow_dates]
#     elif basis_point == 3:
#       cashflow_times = [(date - issue_date).days / 365.0 for date in cashflow_dates]
#
#     # Calculate cash flows
#     cash_flows = np.array([face_value * coupon_rate / frequency] * (len(cashflow_times) - 1) + [face_value * (1 + coupon_rate / frequency)])
#
#     # Discount cash flows to present value
#     discount_factors = np.array([1 / (1 + yield_rate / frequency) ** (frequency * t) for t in cashflow_times])
#     pv_cash_flows = cash_flows * discount_factors
#
#     # Calculate Macaulay Duration
#     maculay_duration = np.sum(np.array(cashflow_times) * pv_cash_flows) / np.sum(pv_cash_flows)
#
#     # Calculate Modified Duration
#     modified_duration = maculay_duration / (1 + yield_rate / frequency)
#
#     return {'status': 'OK', 'duration': maculay_duration, 'modified_duration': modified_duration }
#   except Exception as ex:
#     return {'status': 'ERROR', 'message': str(ex)}

# def calculate_bond(rate_coupon: float = Form(), rate_yield: float = Form(), frequency_count: int = Form(), basis: int = Form(), nominal: float = Form(), issue_date: str = Form(), maturity_date: str = Form()):
#   try:
#     data = pd.DataFrame()
#     # define variable/input
#     yield_rate = rate_yield
#     coupun_rate = rate_coupon
#     period_payment = frequency_count
#     face_value = nominal * 1_000_000_000
#     issue_date = pd.to_datetime(issue_date, format="%Y-%m-%d")
#     maturity_date = pd.to_datetime(maturity_date, format="%Y-%m-%d")
#     # Menghitung selisih tahun
#     time = maturity_date.year - issue_date.year
#
#     # cek apakah bulan dan tanggal maturity date lebih kecil dari tanggal issue date
#     if (maturity_date.month < issue_date.month) or (maturity_date.month == issue_date.month and maturity_date.day < issue_date.day) :
#       time = time - 1 # kurangi 1 jika tidak memenuhi syarat 1 tahun penuh
#
#     # macaulay duration calculation
#     coupun_payment = [(coupun_rate / 2) / 100 * face_value] * (time * period_payment - 1) + [(coupun_rate / 2) / 100 * face_value + face_value]
#     print(coupun_payment)
#
#     total_payment = time * period_payment
#     print(total_payment)
#
#     data['period'] = pd.DataFrame(np.arange(1, total_payment + 1), columns=['period'])
#     print(data)
#
#     data['coupun_payment'] = pd.DataFrame(coupun_payment)
#     print(data)
#
#     data['d_cp'] = data['coupun_payment'] / ((1 + (yield_rate / 2) / 100) ** data['period'])
#     print(data)
#
#     data['pv/total_dcp'] = data['d_cp'] * data['period'] / data['d_cp'].sum()
#     print(data)
#
#     macaulay_duration = data['pv/total_dcp'].sum() / period_payment
#     print(macaulay_duration)
#
#     modified_duration = macaulay_duration / (1 + (yield_rate / 2) / 100)
#     print(modified_duration)
#
#     return {'status': 'OK', 'macaulay_duration': np.round(macaulay_duration, 2), 'modified_duration': np.round(modified_duration, 2) }
#   except Exception as ex:
#     return {'status': 'ERROR', 'message': str(ex)}

@app.post('/api/calculate-bond')
def calculate_bond(rate_coupon: float = Form(), rate_yield: float = Form(), frequency_count: int = Form(), basis: int = Form(), nominal: float = Form(), issue_date: str = Form(), maturity_date: str = Form()):
  try:
    data = pd.DataFrame()
    # define variable/input
    yield_rate = rate_yield
    coupun_rate = rate_coupon
    frequency = frequency_count
    face_value = nominal * 1_000_000_000
    basis_point = basis
    issue_date = pd.to_datetime(issue_date, format="%Y-%m-%d")
    maturity_date = pd.to_datetime(maturity_date, format="%Y-%m-%d")
    # Konstanta untuk basis
    DAYS_IN_YEAR = {
      0: lambda d1, d2: (d2 - d1).days / ((d2.year - d1.year) * 365.25),  # Actual/Actual
      1: lambda d1, d2: ((d2.year - d1.year) * 360 + (d2.month - d1.month) * 30 + (d2.day - d1.day)) / 360,  # 30/360
      2: lambda d1, d2: (d2 - d1).days / 360,  # Actual/360
      3: lambda d1, d2: (d2 - d1).days / 365,  # Actual/365
      4: lambda d1, d2: ((d2.year - d1.year) * 360 + (d2.month - d1.month) * 30 + min(d2.day, 30) - min(d1.day,30)) / 360 # European 30/360
    }

    if basis_point not in DAYS_IN_YEAR:
      return {'status': 'ERROR', 'message': 'Invalid basis. Must be 0, 1, 2, 3, or 4.'}

    # Menghitung waktu hingga jatuh tempo (dalam tahun)
    time_to_maturity = DAYS_IN_YEAR[basis](issue_date, maturity_date)

    # Frekuensi pembayaran bunga per tahun
    total_periods = int(time_to_maturity * frequency)

    coupon_payment = [(rate_coupon / frequency / 100 * face_value)] * (total_periods - 1) + [(rate_coupon / frequency / 100 * face_value + face_value)]
    print(coupon_payment)

    data['period'] = pd.DataFrame(np.arange(1, total_periods + 1), columns=['period'])
    print(data)

    data['coupon_payment'] = pd.DataFrame(coupon_payment)
    print(data)

    # Present Value (PV) dari pembayaran kupon
    discount_factor = (1 + (rate_yield / frequency) / 100)
    data['discounted_cp'] = data['coupon_payment'] / (discount_factor ** data['period'])
    print(data)

    # Menghitung Macaulay Duration
    data['weight'] = data['discounted_cp'] * data['period']
    macaulay_duration = data['weight'].sum() / data['discounted_cp'].sum() / frequency
    print(macaulay_duration)

    # Menghitung Modified Duration
    modified_duration = macaulay_duration / discount_factor
    print(modified_duration)

    return {'status': 'OK', 'macaulay_duration': np.round(macaulay_duration, 2), 'modified_duration': np.round(modified_duration, 2) }
  except Exception as ex:
    return {'status': 'ERROR', 'message': str(ex)}
