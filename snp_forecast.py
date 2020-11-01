# codice python relativo all'articolo presente su datatrading.info
# https://datatrading.info/implementazione-di-una-strategia-di-forecasting-sullsp500/


# snp_forecast.py

import datetime
import pandas as pd
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis as QDA

from strategy.strategy import Strategy
from event.event import SignalEvent
from backtest.backtest import Backtest
from data.data import HistoricCSVDataHandler
from execution.execution import SimulatedExecutionHandler
from portfolio.portfolio import Portfolio
from model.forecast import create_lagged_series

class SPYDailyForecastStrategy(Strategy):
    """
    Strategia previsionale dell'S&P500. Usa un Quadratic Discriminant
    Analyser per prevedere i rendimenti per uno determinato sottoperiodo
    e quindi genera segnali long e di uscita basati sulla previsione.
    """
    def __init__(self, bars, events):
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.datetime_now = datetime.datetime.utcnow()
        self.model_start_date = datetime.datetime(2001,1,10)
        self.model_end_date = datetime.datetime(2005,12,31)
        self.model_start_test_date = datetime.datetime(2005,1,1)
        self.long_market = False
        self.short_market = False
        self.bar_index = 0
        self.model = self.create_symbol_forecast_model()

    def create_symbol_forecast_model(self):
        # Creazione delle serie ritardate dell'indice S&P500
        # del mercato azionario US
        snpret = create_lagged_series(
            self.symbol_list[0], self.model_start_date,
            self.model_end_date, lags=5
        )
        # Uso i rendimenti dei due giorni precedenti come valore
        # previsionale, con direzione come risposta
        X = snpret[["Lag1", "Lag2"]]
        y = snpret["Direction"]
        # Creazione dei set di dati per il training e il test
        start_test = self.model_start_test_date
        X_train = X[X.index < start_test]
        X_test = X[X.index >= start_test]
        y_train = y[y.index < start_test]
        y_test = y[y.index >= start_test]

        model = QDA()
        model.fit(X_train, y_train)
        return model

    def calculate_signals(self, event):
        """
        Calcolo di SignalEvents in base ai dati di mercato.
        """
        sym = self.symbol_list[0]
        dt = self.datetime_now
        if event.type == 'MARKET':
            self.bar_index += 1
            if self.bar_index > 5:
                lags = self.bars.get_latest_bars_values(
                    self.symbol_list[0], "returns", N=3
                )
            pred_series = pd.Series({
                                    'Lag1': lags[1] * 100.0,
                                    'Lag2': lags[2] * 100.0
                                    })
            pred = self.model.predict(pred_series)
            if pred > 0 and not self.long_market:
                self.long_market = True
                signal = SignalEvent(1, sym, dt, 'LONG', 1.0)
                self.events.put(signal)
            if pred < 0 and self.long_market:
                self.long_market = False
                signal = SignalEvent(1, sym, dt, 'EXIT', 1.0)
                self.events.put(signal)

if __name__ == "__main__":
    csv_dir = '/path/to/your/csv/file' # CHANGE THIS!
    symbol_list = ['SPY']
    initial_capital = 100000.0
    heartbeat = 0.0
    start_date = datetime.datetime(2006,1,3)
    backtest = Backtest(
        csv_dir, symbol_list, initial_capital, heartbeat,
        start_date, HistoricCSVDataHandler, SimulatedExecutionHandler,
        Portfolio, SPYDailyForecastStrategy
    )
    backtest.simulate_trading()