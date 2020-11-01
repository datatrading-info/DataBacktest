# https://datatrading.info/sharpe-ratio-per-la-misura-delle-prestazioni-del-trading-algoritmico/

import datetime
import numpy as np
import pandas as pd
from pandas_datareader import data as pdr


def get_historic_data(ticker,
                      start_date=(2000, 1, 1),
                      end_date=datetime.date.today().timetuple()[0:3]):
    """
    Ottenere i dati da Yahoo Finance e li aggiunge a un oggetto DataFrame di Pandas.

    ticker: simbolo del ticker di Yahoo Finanza, ad es. "GOOG" per Google, Inc.
    start_date: data di inizio nel formato (AAAA, M, D)
    end_date: data di fine nel formato (AAAA, M, D)
    """

    start = datetime.datetime(start_date[0], start_date[1], start_date[2])
    end = datetime.datetime(end_date[0], end_date[1], end_date[2])


    pdf = None
    # Prova a connettersi a Yahoo Finance e a ottenere i dati
    # In caso di errore, stampa un messaggio di errore
    try:
        pdf =  pdr.get_data_yahoo(ticker, start, end)
    except Exception as e:
        print("Could not download Yahoo data: {}".format(e))

    return pdf


def annualised_sharpe(returns, N=252):
    """
    Calcola lo Sharpe Ratio annualizzato di un flusso di rendimenti in base
    a un numero di periodi di trading, N. 252 è il valore predefinito per N,
    che quindi presuppone un flusso di rendimenti giornalieri.

    La funzione assume che i rendimenti siano l'eccesso di
    quelli rispetto a un benchmark.
    """
    return np.sqrt(N) * returns.mean() / returns.std()

def equity_sharpe(ticker):
    """
    Calcola l'indice di Sharpe annualizzato in base al quotidiano
    ritorni di un simbolo di ticker azionario elencato in Yahoo Finanza.

    In questo script le date sono state cablate nel codice .
    """

    # Ottenere i dati storici giornalieri delle azioni per il periodo di tempo desiderato
    # e li aggiungi a un DataFrame panda
    pdf = get_historic_data(ticker, start_date=(2000,1,1), end_date=(2016,12,31))

    # Usa il metodo di variazione percentuale per calcolare facilment i rendimenti giornalieri
    pdf['daily_ret'] = pdf['Adj Close'].pct_change()

    # si considera un tasso annuale medio risk-free rate per un periodo del 5%
    pdf['excess_daily_ret'] = pdf['daily_ret'] - 0.05/252

    # restituisce lo Sharpe Ratio annualizzato basato gli eccessi dei rendimenti giornalieri
    return annualised_sharpe(pdf['excess_daily_ret'])

def market_neutral_sharpe(ticker, benchmark):
    """
    Calcola lo Sharpe Ratio annualizzato per una strategia long / short
    neutrale al di un mercato, che prevede di andare long per il 'ticker'
    e un corrispondente short del "benchmark".
    """

    # Ottenere i dati storici sia per un simbolo / ticker che per un benchmark
    # Le date sono state codificate, ma puoi modificarle come meglio credi!
    tick = get_historic_data(ticker, start_date=(2000, 1, 1), end_date=(2016,12,31))
    bench = get_historic_data(benchmark, start_date=(2000, 1, 1), end_date=(2016,12,31))

    # Calcola la percentuale dei rendimenti per ogni serie temporale
    tick['daily_ret'] = tick['Adj Close'].pct_change()
    bench['daily_ret'] = bench['Adj Close'].pct_change()

    # Crea un nuovo DataFrame per memorizzare le informazioni sulla strategia
    # I rendimenti netti sono (long - short) / 2, poiché c'è il doppio
    # capitale di trading per questa strategia
    strat = pd.DataFrame(index=tick.index)
    strat['net_ret'] = (tick['daily_ret'] - bench['daily_ret']) / 2.0

    # restituisce lo Sharpe Ratio annualizzato per questa strategia
    return annualised_sharpe(strat['net_ret'])