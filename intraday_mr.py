# codice python relativo all'articolo presente su datatrading.info
# https://datatrading.info/strategia-di-mean-reversion-per-il-pairs-trading-intraday/


# intraday_mr.py

import datetime
import numpy as np
import pandas as pd
import statsmodels.api as sm

from strategy import Strategy
from event import SignalEvent
from backtest import Backtest

from data import HistoricCSVDataHandlerHFT
from portfolio import PortfolioHFT

from execution import SimulatedExecutionHandler

class IntradayOLSMRStrategy(Strategy):
    """
    Utilizza i minimi quadrati ordinari (OLS) per eseguire una regressione lineare
    continua in modo da determinare il rapporto di hedge tra una coppia di azioni.
    Lo z-score delle serie temporali dei residui viene quindi calcolato in modo
    continuo e se supera un intervallo di soglie (predefinito a [0,5, 3,0]), viene
    generata una coppia di segnali long / short (per la soglia alta) o vengono
    generate coppie di segnali di uscita (per la soglia bassa).
    """
    def __init__(self, bars, events, ols_window=100,zscore_low=0.5, zscore_high=3.0):
        """
        Initializza la strategia di arbitraggio stastistico.
        Parametri:
        bars - L'oggetto DataHandler che fornisce i dati di mercato
        events - L'oggetto Event Queue.
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.ols_window = ols_window
        self.zscore_low = zscore_low
        self.zscore_high = zscore_high
        self.pair = ('AREXQ', 'WLL')
        self.datetime = datetime.datetime.utcnow()
        self.long_market = False
        self.short_market = False


    def calculate_xy_signals(self, zscore_last):
        """
        Calcola le effettive coppie di segnali x, y da inviare al generatore di segnali.

        Parametri
        zscore_last - Il punteggio dello z-score su cui eseguire il test
        """
        y_signal = None
        x_signal = None
        p0 = self.pair[0]
        p1 = self.pair[1]
        dt = self.datetime
        hr = abs(self.hedge_ratio)

        # Se siamo long sul mercato e al di sotto del
        # negativo della soglia alta dello zscore
        if zscore_last <= -self.zscore_high and not self.long_market:
            self.long_market = True
            y_signal = SignalEvent(1, p0, dt, 'LONG', 1.0)
            x_signal = SignalEvent(1, p1, dt, 'SHORT', hr)

        # Se siamo long sul mercato e tra il
        # valore assoluto della soglia bassa dello zscore
        if abs(zscore_last) <= self.zscore_low and self.long_market:
            self.long_market = False
            y_signal = SignalEvent(1, p0, dt, 'EXIT', 1.0)
            x_signal = SignalEvent(1, p1, dt, 'EXIT', 1.0)

        # Se siamo short sul mercato e oltre
        # la soglia alta dello z-score
        if zscore_last >= self.zscore_high and not self.short_market:
            self.short_market = True
            y_signal = SignalEvent(1, p0, dt, 'SHORT', 1.0)
            x_signal = SignalEvent(1, p1, dt, 'LONG', hr)

        # Se siamo short sul mercato e tra il
        # valore assoluto della soglia bassa dello z-score
        if abs(zscore_last) <= self.zscore_low and self.short_market:
            self.short_market = False
            y_signal = SignalEvent(1, p0, dt, 'EXIT', 1.0)
            x_signal = SignalEvent(1, p1, dt, 'EXIT', 1.0)

        return y_signal, x_signal


    def calculate_signals_for_pairs(self):
        """
        Genera una nuova serie di segnali basati sulla strategia di
        ritorno verso la media (mean reversion).
        Calcola il rapporto di hedge tra la coppia di ticker.
        Usiamo OLS per questo, anche se dovremmo idealmente usare il CADF.
        """

        # Otteniamo l'ultima finestra di valori per ogni
        # componente della coppia di ticker
        y = self.bars.get_latest_bars_values(
            self.pair[0], "close", N=self.ols_window
        )
        x = self.bars.get_latest_bars_values(
            self.pair[1], "close", N=self.ols_window
        )

        if y is not None and x is not None:
            # Verificare che tutti i periodi di finestra siano disponibili
            if len(y) >= self.ols_window and len(x) >= self.ols_window:
                # Calcola l'attuale rapporto di hedge utilizzando OLS
                self.hedge_ratio = sm.OLS(y, x).fit().params[0]

                # Calcola l'attuale z-score dei residui
                spread = y - self.hedge_ratio * x
                zscore_last = ((spread - spread.mean()) / spread.std())[-1]

                # Calcula i segnali e il aggiunge alla coda degli eventi
                y_signal, x_signal = self.calculate_xy_signals(zscore_last)
                if y_signal is not None and x_signal is not None:
                    self.events.put(y_signal)
                    self.events.put(x_signal)


    def calculate_signals(self, event):
        """
        Calcula il SignalEvents basato sui dati di mercato.
        """
        if event.type == 'MARKET':
            self.calculate_signals_for_pairs()


if __name__ == "__main__":
    #csv_dir = '/path/to/your/csv/file' # DA MODIFICARE
    csv_dir = 'csv_files'  # DA MODIFICARE
    symbol_list = ['AREXQ', 'WLL']
    initial_capital = 100000.0
    heartbeat = 0.0
    start_date = datetime.datetime(2008, 11, 8, 10, 41, 0)

    backtest = Backtest(
        csv_dir, symbol_list, initial_capital, heartbeat,start_date,
        HistoricCSVDataHandlerHFT, SimulatedExecutionHandler,
        PortfolioHFT, IntradayOLSMRStrategy
    )
    backtest.simulate_trading()