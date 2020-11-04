# codice python relativo all'articolo presente su datatrading.info
# https://datatrading.info/implementazione-di-una-strategia-di-moving-average-crossover/

# mac.py

import datetime
import numpy as np
import pandas as pd
import statsmodels.api as sm

from strategy import Strategy
from event import SignalEvent
from backtest import Backtest
from data import HistoricCSVDataHandler
from execution import SimulatedExecutionHandler
from portfolio import NaivePortfolio

class MovingAverageCrossStrategy(Strategy):
    """
    Esegue una strategia base di Moving Average Crossover tra due
    medie mobile semplici, una breve e una lunga. Le finestre brevi / lunghe
    sono rispettivamente di 100/400 periodi.
    """
    def __init__(self, bars, events, short_window=100, long_window=400):
        """
        Initializza la strategia di Moving Average Cross.

        Parametri:
        bars - L'oggetto DataHandler object che fornisce le barre dei prezzi
        events - L'oggetto Event Queue.
        short_window - Il periodo per la media mobile breve.
        long_window - Il periodo per la media mobile lunga.
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.short_window = short_window
        self.long_window = long_window

        # Impostato a True se la strategia è a mercato
        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        """
        Aggiunge keys per ogni simbolo al dizionario bought e le
        imposta a 'OUT'.
        """
        bought = {}
        for s in self.symbol_list:
            bought[s] = 'OUT'
            return bought

    def calculate_signals(self, event):
        """
        Genera un nuovo set di segnali basato sull'incrocio della
        SMA di breve periodo con quella a lungo periodo che
        significa un'entrata long e viceversa per un'entrata short.

        Parametri
        event - Un oggetto MarketEvent.
        """
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars_values(
                    s, "adj_close", N=self.long_window
                )
                bar_date = self.bars.get_latest_bar_datetime(s)
                if bars is not None and bars != []:
                    short_sma = np.mean(bars[-self.short_window:])
                    long_sma = np.mean(bars[-self.long_window:])
                    symbol = s
                    dt = datetime.datetime.utcnow()
                    sig_dir = ""
                    if short_sma > long_sma and self.bought[s] == "OUT":
                        print("LONG: %s" % bar_date)
                        sig_dir = 'LONG'

                        signal = SignalEvent(1, symbol, dt, sig_dir, 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'LONG'
                    elif short_sma < long_sma and self.bought[s] == "LONG":
                        print("SHORT: %s" % bar_date)
                        sig_dir = 'EXIT'
                        signal = SignalEvent(1, symbol, dt, sig_dir, 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'OUT'


if __name__ == "__main__":
    csv_dir = '/path/to/your/csv/file' # DA MODIFICARE
    csv_dir = 'csv_files'
    symbol_list = ['AAPL']
    initial_capital = 100000.0
    heartbeat = 0.0
    start_date = datetime.datetime(1990, 1, 1, 0, 0, 0)
    backtest = Backtest(csv_dir, symbol_list, initial_capital, heartbeat, start_date,
                        HistoricCSVDataHandler, SimulatedExecutionHandler, NaivePortfolio,
                        MovingAverageCrossStrategy)
    backtest.simulate_trading()
