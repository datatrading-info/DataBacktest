#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Per ottenere i dati storici degli attuali titoli che compongono l'S&P500, dobbiamo prima
interrogare il database per farci restituire l'elenco di tutti i simboli. Una volta ottenuto
l'elenco dei simboli (insieme agli ID dei simboli), è possibile richiamare l'API di Yahoo
Finance e scaricare lo storico dei prezzi da ciascun simbolo.
Quindi possiamo inserire i dati nel database per ogni simboli ottenuto.
Ecco il codice Python che effettua queste operazioni:
"""

import datetime
import pymysql as mdb
from urllib.request import urlopen

# create una connessione ad un'instanza del database MySQL
db_host = 'localhost'
db_user = 'sec_user'
db_pass = 'password'
db_name = 'securities_master'
con = mdb.connect(db_host, db_user, db_pass, db_name)


def obtain_list_of_db_tickers():
    """Ottenere una lista di ticker dalla tabella Symbols del database."""
    with con:
        cur = con.cursor()
        cur.execute("SELECT id, ticker FROM symbol")
        data = cur.fetchall()
        return [(d[0], d[1]) for d in data]


def get_daily_historic_data_yahoo(ticker,
                                  start_date=(2000, 1, 1),
                                  end_date=datetime.date.today().timetuple()[0:3]):
    """
    Ricavare i dati da Yahoo Finance e restituisce una lista di tuple.

    ticker: simbolo di un ticker di Yahoo Finance, e.g. "GOOG" for Google, Inc.
    start_date: data iniziale nel formato (YYYY, M, D)
    end_date: data finale nel formato (YYYY, M, D)
    """

    # Construzione del URL di Yahoo con la corretta query di parametri integer
    # per le date di inizio e fine. Da notare che alcuni parametri sono base zero!
    yahoo_url = "http://ichart.finance.yahoo.com/table.csv?s=%s&a=%s&b=%s&c=%s&d=%s&e=%s&f=%s" % \
                (ticker, start_date[1] - 1, start_date[2], start_date[0], end_date[1] - 1, end_date[2], end_date[0])

    # Prova di connessione a Yahoo Finance e ottenere i dati
    # In caso di mancata ricezione si stampa un messaggio di errore.
    try:
        yf_data = urlopen(yahoo_url).readlines()[1:]  # Ignora l'header
        prices = []
        for y in yf_data:
            p = y.strip().split(',')
            prices.append((datetime.datetime.strptime(p[0], '%Y-%m-%d'),
                           p[1], p[2], p[3], p[4], p[5], p[6]))
    except Exception as e:
        print("Could not download Yahoo data: %s" % e)
    return prices


def insert_daily_data_into_db(data_vendor_id, symbol_id, daily_data):
    """
    Prende una lista di tuples di dati giornalieri e il inserisce nel
    database MySQL. Si aggiunge un vendor ID e un symbol ID nei dati.

    daily_data: Lista di tuples di dati OHLC (con adj_close e volume)
    """

    # Ottenere l'ora attuale
    now = datetime.datetime.utcnow()

    # Creazione dei dati giornalieri con vendor ID e symbol ID
    daily_data = [(data_vendor_id, symbol_id, d[0], now, now,
                   d[1], d[2], d[3], d[4], d[5], d[6]) for d in daily_data]

    # Creazione delle stringhe di insert
    column_str = """data_vendor_id, symbol_id, price_date, created_date, 
          last_updated_date, open_price, high_price, low_price, 
          close_price, volume, adj_close_price"""
    insert_str = ("%s, " * 11)[:-2]
    final_str = "INSERT INTO daily_price (%s) VALUES (%s)" % (column_str, insert_str)

    # Uso della connessione di MySQL per eseguire un INSERT INTO per ogni simbolo
    with con:
        cur = con.cursor()
        cur.executemany(final_str, daily_data)


if __name__ == "__main__":
    # Ciclo su tutti i ticker e inserimento dei dati storici
    # giornalieri nel database
    tickers = obtain_list_of_db_tickers()
    for t in tickers:
        print("Adding data for %s" % t[1])
        yf_data = get_daily_historic_data_yahoo(t[1])
        insert_daily_data_into_db('1', t[0], yf_data)