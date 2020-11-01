
# codice python relativo all'articolo presente su datatrading.info
# https://datatrading.info/motore-di-backtesting-con-python-parte-iii-dati-di-mercato/

# data.py

import datetime
import os, os.path
import pandas as pd
import numpy as np

from abc import ABCMeta, abstractmethod

from event.event import MarketEvent



class DataHandler(object):
    """
    DataHandler è una classe base astratta che fornisce un'interfaccia per
    tutti i successivi  gestori di dati (ereditati) (sia live che storici).

    L'obiettivo di un oggetto (derivato da) DataHandler è generare un
    set di barre (OLHCVI) per ogni simbolo richiesto.

    Questo replicherà il modo in cui una strategia live funzionerebbe quando nuovi
    i dati di mercato sarebbero inviati "giù per il tubo". Questo permette a sistemi
    live e a sistemi con dati storici di essere trattati allo stesso modo dal resto
    della suite di backtest.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_latest_bar(self, symbol):
        """
        Restituisce l'ultima barra dalla lista latest_symbol.
        """
        raise NotImplementedError("Should implement get_latest_bar()")

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """
        Restituisce le ultime N barre dalla lista di barre
        per il simbolo, o meno se sono disponibili poche barre
        """
        raise NotImplementedError("Should implement get_latest_bars()")

    def get_latest_bar(self, symbol):
        """
        Restituisce l'ultima barra dalla lista latest_symbol.
        """
        raise NotImplementedError("Should implement get_latest_bar()")

    @abstractmethod
    def get_latest_bar_datetime(self, symbol):
        """
        Restituisce un oggetto datetime di Python per l'ultima barra.
        """
        raise NotImplementedError("Should implement get_latest_bar_datetime()")\


    @abstractmethod
    def get_latest_bar_value(self, symbol, val_type):
        """
        Restituisce un elemento tra Open, High, Low, Close, Volume o Adj_Close
        from the last bar.
        """
        raise NotImplementedError("Should implement get_latest_bar_value()")


    @abstractmethod
    def get_latest_bars_values(self, symbol, val_type, N=1):
        """
        Restituisce i valori delle ultime N barre dalla lista
        latest_symbol, o N-k se non meno disponibili.
        """
        raise NotImplementedError("Should implement get_latest_bars_values()")

    @abstractmethod
    def update_bars(self):
        """
        Inserisce la barra più recente nella struttura delle barre per
        tutti i simboli della lista di simboli.
        """
        raise NotImplementedError("Should implement update_bars()")



class HistoricCSVDataHandler(DataHandler):
    """
    HistoricCSVDataHandler è progettato per leggere dal disco
    fisso un file CSV per ogni simbolo richiesto e fornire
    un'interfaccia per ottenere la barra "più recente" in un
    modo identico a un'interfaccia di live trading.
    """

    def __init__(self, events, csv_dir, symbol_list):
        """
        Inizializza il gestore dei dati storici richiedendo
        la posizione dei file CSV e un elenco di simboli.

        Si presume che tutti i file abbiano la forma
        "symbol.csv", dove symbol è una stringa dell'elenco.

        Parametri:
        events - la coda degli eventi.
        csv_dir - percorso assoluto della directory dei file CSV.
        symbol_list - Un elenco di stringhe di simboli.
        """

        self.events = events
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list

        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True

        self._open_convert_csv_files()


    def _open_convert_csv_files(self):
        """
        Apre i file CSV dalla directory dei dati, convertendoli
        in DataFrame pandas all'interno di un dizionario di simboli.

        Per questo gestore si assumerà che i dati siano
        tratto da DTN IQFeed. Così il suo formato sarà rispettato.
        """
        comb_index = None
        for s in self.symbol_list:
            # Carica il file CSV senza nomi delle colonne, indicizzati per data
            self.symbol_data[s] = pd.io.parsers.read_csv(
                                      os.path.join(self.csv_dir, '%s.csv' % s),
                                      header=0, index_col=0, parse_dates=True,
                                      names=['datetime','open','low','high',
                                             'close','adj_close','volume']
                                  )

            # Combina l'indice per riempire i valori successivi
            if comb_index is None:
                comb_index = self.symbol_data[s].index
            else:
                comb_index.union(self.symbol_data[s].index)

            # Imposta il più recente symbol_data a None
            self.latest_symbol_data[s] = []

        # Indicizza nuovamente i dataframes
        for s in self.symbol_list:
            self.symbol_data[s] = self.symbol_data[s].reindex(index=comb_index, method='pad').iterrows()


    def _get_new_bar(self, symbol):
        """
        Restituisce l'ultima barra dal feed di dati come una tupla di
        (sybmbol, datetime, open, low, high, close, volume).
        """
        for b in self.symbol_data[symbol]:
            yield b


    def get_latest_bar(self, symbol):
        """
        Restituisce l'ultima barra dalla lista latest_symbol.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1]


    def get_latest_bars(self, symbol, N=1):
        """
        Restituisce le ultime N barre dall'elenco latest_symbol
        o N-k se non sono tutte disponibili.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
        else:
            return bars_list[-N:]


    def get_latest_bar_datetime(self, symbol):
        """
        Restituisce un oggetto datetime di Python per l'ultima barra.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1][0]

    def get_latest_bar_value(self, symbol, val_type):
        """
        Restituisce un elemento tra Open, High, Low, Close, Volume o Adj_Close
        from the last bar.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return getattr(bars_list[-1][1], val_type)


    def get_latest_bars_values(self, symbol, val_type, N=1):
        """
        Restituisce i valori delle ultime N barre dalla lista
        latest_symbol, o N-k se non meno disponibili.
        """
        try:
            bars_list = self.get_latest_bars(symbol, N)
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return np.array([getattr(b[1], val_type) for b in bars_list])

    @abstractmethod
    def update_bars(self):
        """
        Inserisce la barra più recente nella struttura delle barre per
        tutti i simboli della lista di simboli.
        """

    def update_bars(self):
        """
        Inserisce l'ultima barra nella struttura latest_symbol_data
        per tutti i simboli nell'elenco dei simboli.
        """
        for s in self.symbol_list:
            try:
                bar = next(self._get_new_bar(s))
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar)
        self.events.put(MarketEvent())