#!/usr/bin/python
# -*- coding: utf-8 -*-

import pandas as pd
import pandas.io.sql as psql
import pymysql as mdb


# Connessione all'instanza di MySQL
db_host = 'localhost'
db_user = 'sec_user'
db_pass = 'password'
db_name = 'securities_master'
con = mdb.connect(db_host, db_user, db_pass, db_name)

# Selezione di tutti i dati storici di Google con il campo "adjusted close"
sql = """SELECT dp.price_date, dp.adj_close_price
         FROM symbol AS sym
         INNER JOIN daily_price AS dp
         ON dp.symbol_id = sym.id
         WHERE sym.ticker = 'GOOG'
         ORDER BY dp.price_date ASC;"""

# Creazione di un dataframe pandas dalla query SQL
goog = psql.frame_query(sql, con=con, index_col='price_date')

# Stampa della coda del dataframe
print(goog.tail())