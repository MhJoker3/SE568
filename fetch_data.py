import pip
import os
try:
    import mysql.connector  # using mysql connector should install it first(python 2.7/3.3/3.4)
except ImportError:
    print('Please Install MySQL Connector(Python) First.')
    raise SystemExit()

try:
    import pandas as pd
    from pandas import DataFrame
except ImportError:
    pip.main(['install', 'pandas'])
    import pandas as pd

try:
    import pandas_datareader as pdr
    from pandas_datareader import data, wb
except ImportError:
    pip.main(['install', 'pandas_datareader'])
    import pandas_datareader as pdr
    from pandas_datareader import data, wb

try:
    from sqlalchemy import create_engine
    from sqlalchemy.types import VARCHAR
except ImportError:
    pip.main(['install', 'sqlalchemy'])
    from sqlalchemy import create_engine
    from sqlalchemy.types import VARCHAR

try:
    from datetime import *
except ImportError:
    pip.main(['install', 'datetime'])
    from datetime import *

try:
    from alpha_vantage.timeseries import TimeSeries
except ImportError:
    pip.main(['install', 'alpha_vantage'])
    from alpha_vantage.timeseries import TimeSeries

import time

User = 'admin'
PassWord = 'password'
Host = 'se568.csfmbtsxk6dc.us-east-2.rds.amazonaws.com'
Port = '3306'
Database = 'SEProject'
api_key = 'EQ6GGWD5D4ME4283'

try:
    cnx = mysql.connector.connect(user=User, password=PassWord, host=Host)  # using configuration of sever
except mysql.connector.Error:
    print('Can Not Connect With Database Sever.')
    raise SystemExit()

cursor = cnx.cursor()

# using mysql to create real time data
create_RealtimeData = '''CREATE TABLE IF NOT EXISTS realtimedata               
                       (`date` DATETIME,
                        `open` REAL,
                        `high` REAL,
                        `low` REAL,
                        `close` REAL,
                        `volume` INTEGER,
                        `sym` CHAR(20),
                        PRIMARY KEY(sym,date)
                        );'''

# using mysql to creat historical data
create_HistoricalData = '''CREATE TABLE IF NOT EXISTS historicaldata
                       (`date` DATE,
                        `open` REAL,
                        `high` REAL,
                        `low` REAL,
                        `close` REAL,
                        `volume` INTEGER,
                        `sym` CHAR(20),
                        PRIMARY KEY(sym,date)
                        );'''
cursor.execute('CREATE DATABASE IF NOT EXISTS ' + Database)  # creat database if not exists
cursor.execute('USE ' + Database)  # select the database
cursor.execute(create_RealtimeData)  # create table
cursor.execute(create_HistoricalData)  # create table

# end and start dates for the historical quotes
end = date.today()
start = end - timedelta(days=365)  # this calculates exactly a year back from today

# get TimeSeries object of Alpha Vintage API
ts = TimeSeries(key=api_key,output_format='pandas')


print('Reading Data and Putting them in Database. Exit with Ctrl+C.')
try:
    # returns current price and volume quotes for a given symbol in a dataframe
    def get_realtime_data(stock):
        realtime = []
        for ticker in stock:
            df, meta = ts.get_intraday(symbol=ticker, interval='1min', outputsize='full')
            df['sym'] = meta['2. Symbol']
            realtime.append(df)
        return realtime

    def get_hist_data(stock):
        historical = []
        for ticker in stock:
            # print("loading " + ticker)
            df, meta = ts.get_daily(symbol=ticker, outputsize='full')
            df['sym'] = meta['2. Symbol']
            historical.append(df)
        return historical

    engine = create_engine('mysql+mysqlconnector://' + User + ':' + PassWord + '@' + Host + ':' + Port + '/' + Database,
                           echo=False)

    # using alpha vantage finance api to save data into a pandas dataframe
    stocks = ['AAPL', 'GOOGL', 'NVDA', 'TSLA', 'AMZN', 'MSFT', 'BAC', 'NKE', 'NFLX', 'FB']
    # stocks = ['AAPL']
    df_historical = get_hist_data(stocks)
    print('Creating historical database.')
    for i in range(0, len(stocks)):
        df = df_historical[i]
        if not os.path.exists('data'):
            os.makedirs('data')
        df.to_csv('data/' + stocks[i] + '_historical.csv')
        if i == 0:
            df.to_sql(name='historicaldata', con=engine, if_exists='replace', dtype={'date': VARCHAR(df.index.get_level_values('date').str.len().max())})
        else:
            df.to_sql(name='historicaldata', con=engine, if_exists='append')

    # ============= code for real-time quotes ==============
    print('Loading real-time data.')
    df_realtime = get_realtime_data(stocks)
    for i in range(0, len(stocks)):
        df = df_realtime[i]
        df.to_csv('data/' + stocks[i] + '_rtdata.csv')
        if i == 0:
            df.to_sql(name='realtimedata', con=engine, if_exists='replace', dtype={'date': VARCHAR(df.index.get_level_values('date').str.len().max())})
        else:
            df.to_sql(name='realtimedata', con=engine, if_exists='append')

    # while True:
    #     print('Continue loading.')
    #     df_realtime = get_realtime_data(stocks)
    #     for i in range(len(stocks)):
    #         df_newest = pd.DataFrame(df_realtime[i].iloc[-1:])
    #         print(df_newest)
    #         with open('data/' + stocks[i] + '_rtdata.csv', 'a') as file:
    #             df_newest.to_csv(file, header=False, index=True)
    #         df_newest.to_sql(name='realtimedata', con=engine, if_exists='append')
    #
    #     time.sleep(10)

except KeyboardInterrupt:
    print('User Asked to Exit')
    raise SystemExit()
finally:
    cnx.close()  # close the connector
