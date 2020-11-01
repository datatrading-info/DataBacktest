#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import lxml.html
import pymysql as mdb

from math import ceil

"""
Iniziamo con il recuperare i simboli associati all'elenco di Standard & Poor's dei 500 titoli a grande 
capitalizzazione, ad esempio S&P500. Naturalmente, questo è semplicemente un esempio. 
Se stai operando sul mercato italiano e desideri utilizzare gli indici domestici dell'Italia, puoi anche 
ottenere l'elenco delle società FTSE MIB quotate alla Borsa di Milano (LSE).

Inoltre Wikipedia elenca le componenti del S&P500. Analizzeremo questo sito web usando la libreria lxml 
di Python ed aggiungeremo direttamente il contenuto direttamente al database in MySQL. 
"""

def obtain_parse_wiki_snp500():
    """
    Scarica e analizza l'elenco dei costituenti
    dell'S&P500 da Wikipedia utilizzando le librerie
    requests e libxml.

    Restituisce un elenco di tuple da aggiungere a al
    database MySQL.
    """

    # Memorizza l'ora corrente, per il record created_at
    now = datetime.datetime.utcnow()

    # Usa libxml per scaricare l'elenco delle società S&P500 e ottenere la tabella dei simboli
    page = lxml.html.parse('http://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    symbolslist = page.xpath('//table[1]/tr')[1:]

    # Ottenere le informazioni sui simboli per ogni riga nella tabella dei componenti S&P500
    symbols = []
    for symbol in symbolslist:
        tds = symbol.getchildren()
        sd = {'ticker': tds[0].getchildren()[0].text,
            'name': tds[1].getchildren()[0].text,
            'sector': tds[3].text}

        # Crea una tupla (per il formato DB) e la aggiunge alla lista
        symbols.append( (sd['ticker'], 'stock', sd['name'],
          sd['sector'], 'USD', now, now) )
    return symbols

def insert_snp500_symbols(symbols):
    """Inserimento dei simboli dell'S&P500 nel database MySQL."""

    # Connessione all'instanza di MySQL
    db_host = 'localhost'
    db_user = 'sec_user'
    db_pass = 'password'
    db_name = 'securities_master'
    con = mdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)

    # Creazione delle stringe per l'insert
    column_str = "ticker, instrument, name, sector, currency, created_date, last_updated_date"
    insert_str = ("%s, " * 7)[:-2]
    final_str = "INSERT INTO symbol (%s) VALUES (%s)" % (column_str, insert_str)
    print(final_str, len(symbols))

    # Usando la connessione MySQL, si effettua un INSERT INTO per ogni simbolo
    with con:
        cur = con.cursor()
        # Questa riga evita MySQL MAX_PACKET_SIZE
        # Anche se ovviamente potrebbe essere impostato più grande!
        for i in range(0, int(ceil(len(symbols) / 100.0))):
            cur.executemany(final_str, symbols[i*100:(i+1)*100-1])

if __name__ == "__main__":
    symbols = obtain_parse_wiki_snp500()
    insert_snp500_symbols(symbols)