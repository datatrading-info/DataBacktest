
# codice python relativo all'articolo presente su datatrading.info
# https://datatrading.info/motore-di-backtesting-con-python-parte-viii-backtest/

# backtest.py

import datetime
import pprint

import queue
import time

class Backtest(object):
    """
    Racchiude le impostazioni e i componenti per l'esecuzione
    un backtest basato sugli eventi.
    """
    def __init__(self, csv_dir, symbol_list, initial_capital,
                 heartbeat, start_date, data_handler,
                 execution_handler, portfolio, strategy):
        """
        Inizializza il backtest.

        Parametri:
        csv_dir - Il percorso della directory dei dati CSV.
        symbol_list - L'elenco dei simboli.
        intial_capital - Il capitale iniziale del portafoglio.
        heartbeat - il "battito cardiaco" del backtest in secondi
        data_inizio - La data e ora di inizio della strategia.
        data_handler - (Classe) Gestisce il feed di dati di mercato.
        execution_handler - (Classe) Gestisce gli ordini / esecuzioni per i trade.
        portfolio - (Classe) Tiene traccia del portafoglio attuale e delle posizioni precedenti.
        strategy - (Classe) Genera segnali basati sui dati di mercato.
        """

        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.heartbeat = heartbeat
        self.start_date = start_date
        self.data_handler_cls = data_handler
        self.execution_handler_cls = execution_handler
        self.portfolio_cls = portfolio
        self.strategy_cls = strategy
        self.events = queue.Queue()
        self.signals = 0
        self.orders = 0
        self.fills = 0
        self.num_strats = 1
        self._generate_trading_instances()


    def _generate_trading_instances(self):
        """
        Genera le istanze degli componenti del backtest a partire dalle loro classi.
        """

        print("Creating DataHandler, Strategy, Portfolio and ExecutionHandler")
        self.data_handler = self.data_handler_cls(self.events,
                                                  self.csv_dir,
                                                  self.symbol_list)
        self.strategy = self.strategy_cls(self.data_handler,
                                          self.events)
        self.portfolio = self.portfolio_cls(self.data_handler,
                                            self.events,
                                            self.start_date,
                                            self.initial_capital)
        self.execution_handler = self.execution_handler_cls(self.events)


    def _run_backtest(self):
        """
        Esecuzione del backtest.
        """
        i = 0
        while True:
            i += 1
            print(i)
            # Aggiornamento dei dati di mercato
            if self.data_handler.continue_backtest == True:
                self.data_handler.update_bars()
            else:
               break
            # Gestione degli eventi
            while True:
                try:
                    event = self.events.get(False)
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == 'MARKET':
                            self.strategy.calculate_signals(event)
                            self.portfolio.update_timeindex(event)
                        elif event.type == 'SIGNAL':
                            self.signals += 1
                            self.portfolio.update_signal(event)
                        elif event.type == 'ORDER':
                            self.orders += 1
                            self.execution_handler.execute_order(event)
                        elif event.type == 'FILL':
                            self.fills += 1
                            self.portfolio.update_fill(event)
            time.sleep(self.heartbeat)


    def _output_performance(self):
        """
        Stampa delle performance della strategia dai risultati del backtest.
        """
        self.portfolio.create_equity_curve_dataframe()
        print("Creating summary stats...")
        stats = self.portfolio.output_summary_stats()
        print("Creating equity curve...")
        print(self.portfolio.equity_curve.tail(10))
        pprint.pprint(stats)
        print("Signals: %s" % self.signals)
        print("Orders: %s" % self.orders)
        print("Fills: %s" % self.fills)

    def simulate_trading(self):
        """
        Simula il backtest e stampa le performance del portafoglio.
        """
        self._run_backtest()
        self._output_performance()