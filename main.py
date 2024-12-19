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
import QuantLib as ql

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
# def calculate_bond(rate_coupon: float = Form(), rate_yield: float = Form(), frequency_count: int = Form(), basis: int = Form(), nominal: float = Form(), settlement_date: str = Form(), maturity_date: str = Form()):
#   try:
#     data = pd.DataFrame()
#     # define variable/input
#     yield_rate = rate_yield
#     coupun_rate = rate_coupon
#     frequency = frequency_count
#     face_value = nominal * 1_000_000_000
#     basis_point = basis
#     settlement_date = pd.to_datetime(settlement_date, format="%Y-%m-%d")
#     maturity_date = pd.to_datetime(maturity_date, format="%Y-%m-%d")
#
#     def nasd_30_360(start_date, end_date):
#       # Ekstrak tahun, bulan, dan hari dari tanggal
#       y1, m1, d1 = start_date.year, start_date.month, start_date.day
#       y2, m2, d2 = end_date.year, end_date.month, end_date.day
#
#       # Aturan NASD untuk hari
#       if d1 == 31:
#         d1 = 30
#       if d2 == 31 and d1 == 30:
#         d2 = 30
#
#       # Aturan NASD untuk Februari
#       if m1 == 2 and d1 == 28 + (1 if ((y1 % 4 == 0 and y1 % 100 != 0) or y1 % 400 == 0) else 0):
#         d1 = 30
#
#       if m2 == 2 and d2 == 28 + (1 if ((y2 % 4 == 0 and y2 % 100 != 0) or y2 % 400 == 0) else 0):
#         d2 = 30
#
#         # Hitung jumlah hari dengan basis 30/360
#       return ((y2 - y1) * 360 + (m2 - m1) * 30 + (d2 - d1)) / 360.0
#
#     # Konstanta untuk basis
#     DAYS_IN_YEAR = {
#       0: lambda d1, d2: (d2 - d1).days / ((d2.year - d1.year) * 365.25),  # Actual/Actual
#       #1: lambda d1, d2: ((d2.year - d1.year) * 360.0 + (d2.month - d1.month) * 30 + (d2.day - d1.day)) / 360.0,  # 30/360
#       1: lambda d1, d2: nasd_30_360(d1, d2),
#       2: lambda d1, d2: (d2 - d1).days / 360.0,  # Actual/360
#       3: lambda d1, d2: (d2 - d1).days / 365.0,  # Actual/365
#       4: lambda d1, d2: ((d2.year - d1.year) * 360 + (d2.month - d1.month) * 30 + min(d2.day, 30) - min(d1.day,30)) / 360 # European 30/360
#     }
#     # DAYS_IN_YEAR = {
#     #   0: lambda d1, d2: ((d2.year - d1.year) +(d2.month - d1.month) / 12.0 + (min(d2.day, 30) - min(d1.day, 30)) / 360.0),  # 30/360 US
#     #   1: lambda d1, d2: (d2 - d1).days / 365.0,  # Actual/Actual
#     #   2: lambda d1, d2: (d2 - d1).days / 360.0,  # Actual/360
#     #   3: lambda d1, d2: (d2 - d1).days / 365.0,  # Actual/365
#     #   4: lambda d1, d2: ((d2.year - d1.year) + (d2.month - d1.month) / 12.0 + (min(d2.day, 30) - min(d1.day, 30)) / 360.0) # European 30/360
#     # }
#
#     if basis_point not in DAYS_IN_YEAR:
#       return {'status': 'ERROR', 'message': 'Invalid basis. Must be 0, 1, 2, 3, or 4.'}
#
#     # Menghitung waktu hingga jatuh tempo (dalam tahun)
#     time_to_maturity = DAYS_IN_YEAR[basis](settlement_date, maturity_date)
#
#     # Frekuensi pembayaran bunga per tahun
#     total_periods = math.floor(time_to_maturity * frequency)
#
#     coupon_payment = [((coupun_rate / frequency) / 100 * face_value)] * (total_periods - 1) + [((coupun_rate / frequency) / 100 * face_value + face_value)]
#     print(coupon_payment)
#
#     data['period'] = pd.DataFrame(np.arange(1, total_periods + 1), columns=['period'])
#     print(data)
#
#     data['coupon_payment'] = pd.DataFrame(coupon_payment)
#     print(data)
#
#     # Present Value (PV) dari pembayaran kupon
#     discount_factor = (1 + (rate_yield / frequency) / 100)
#     data['discounted_cp'] = data['coupon_payment'] / (discount_factor ** data['period'])
#     print(data)
#
#     # Menghitung Macaulay Duration
#     data['weight'] = data['discounted_cp'] * data['period']
#     macaulay_duration = data['weight'].sum() / data['discounted_cp'].sum() / frequency
#     print(macaulay_duration)
#
#     # Menghitung Modified Duration
#     modified_duration = macaulay_duration / discount_factor
#     print(modified_duration)
#
#     return {'status': 'OK', 'macaulay_duration': np.round(macaulay_duration, 2), 'modified_duration': np.round(modified_duration, 2) }
#   except Exception as ex:
#     return {'status': 'ERROR', 'message': str(ex)}

@app.post('/api/calculate-bond')
def calculate_bond(rate_coupon: float = Form(), rate_yield: float = Form(), frequency_count: int = Form(), basis: int = Form(), nominal: float = Form(), settlement_date: str = Form(), maturity_date: str = Form()):
  try:
    data = pd.DataFrame()
    # define variable/input
    yield_rate = rate_yield / 100
    coupun_rate = rate_coupon / 100
    frequency = frequency_count
    face_value = float(nominal * 1_000_000_000)
    basis_point = basis
    settlement_date = pd.to_datetime(settlement_date, format="%Y-%m-%d")
    maturity_date = pd.to_datetime(maturity_date, format="%Y-%m-%d")

    ql_settlement_date = ql.Date(settlement_date.day, settlement_date.month, settlement_date.year)
    ql_maturity_date = ql.Date(maturity_date.day, maturity_date.month, maturity_date.year)

    ql.Settings.instance().evaluationDate = ql_settlement_date

    freq = {
      1: ql.Annual,
      2: ql.Semiannual,
      4: ql.Quarterly,
    }

    basis = {
      0: ql.Actual360(),
      1: ql.ActualActual(ql.ActualActual.ISDA),
      2: ql.Actual360(),
      3: ql.Actual365Fixed(),
      4: ql.Thirty360(ql.Thirty360.BondBasis)
    }

    frequency = freq.get(frequency, ql.Annual)
    tenor = ql.Period(frequency)
    business_convention = ql.Unadjusted
    calendar = ql.NullCalendar()
    date_generation = ql.DateGeneration.Forward
    basis_point = basis.get(basis_point, ql.ActualActual(ql.ActualActual.ISDA))

    # create the schedule for the bond
    schedule = ql.Schedule(
      ql_settlement_date,
      ql_maturity_date,
      tenor,
      calendar,
      business_convention,
      business_convention,
      date_generation,
      False
    )

    # define the fixed-rate bond
    coupons = [coupun_rate]
    fixed_rate_bonds = ql.FixedRateBond(
      0,
      face_value,
      schedule,
      coupons,
      basis_point,
    )

    simple_quote = ql.SimpleQuote(yield_rate)
    quote_handle = ql.QuoteHandle(simple_quote)
    compounding = ql.Compounded

    # set up the yield curve (discounting term structure)
    flat_forward = ql.FlatForward(ql_settlement_date, quote_handle, basis_point, compounding, frequency)
    yield_rate_handle = ql.YieldTermStructureHandle(flat_forward)

    # set up the bond pricing engine
    bond_engine = ql.DiscountingBondEngine(yield_rate_handle)
    fixed_rate_bonds.setPricingEngine(bond_engine)

    # calculating yields
    target_price = fixed_rate_bonds.cleanPrice()
    ytm = fixed_rate_bonds.bondYield(target_price, basis_point, compounding, frequency)

    # calculating interest rate
    rate = ql.InterestRate(ytm, basis_point, compounding, frequency)

    # calculate durations
    macaulay_duration = ql.BondFunctions.duration(fixed_rate_bonds, rate, ql.Duration.Macaulay)
    modified_duration = ql.BondFunctions.duration(fixed_rate_bonds, rate, ql.Duration.Modified)

    return {'status': 'OK', 'macaulay_duration': np.round(macaulay_duration, 2), 'modified_duration': np.round(modified_duration, 2)}
  except Exception as ex:
    return {'status': 'ERROR', 'message': str(ex)}
