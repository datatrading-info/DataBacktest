
# codice python relativo all'articolo presente su datatrading.info
# https://datatrading.info/motore-di-backtesting-con-python-parte-v-portafoglio/



# portfolio.py

import datetime
import numpy as np
import pandas as pd
import queue

from abc import ABCMeta, abstractmethod
from math import floor

from event.event import FillEvent, OrderEvent
from performance.performance import create_sharpe_ratio, create_drawdowns

# portfolio.py

class Portfolio(object):
    """
    La classe Portfolio gestisce le posizioni e il valore di
    mercato di tutti gli strumenti alla risoluzione di una "barra",
    cioè ogni secondo, ogni minuto, 5 minuti, 30 minuti, 60 minuti o EOD.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def update_signal(self, event):
        """
        Azioni su un SignalEvent per generare nuovi ordini
        basati sulla logica di portafoglio
        """
        raise NotImplementedError("Should implement update_signal()")

    @abstractmethod
    def update_fill(self, event):
        """
        Aggiorna le posizioni e il patrimonio del portafoglio
        da un FillEvent.
        """
        raise NotImplementedError("Should implement update_fill()")


class NaivePortfolio(Portfolio):
    """
    L'oggetto NaivePortfolio è progettato per inviare ordini a
    un oggetto di intermediazione con una dimensione di quantità costante,
    cioè senza alcuna gestione del rischio o dimensionamento della posizione. È
    utilizzato per testare strategie più semplici come BuyAndHoldStrategy.
    """

    def __init__(self, bars, events, start_date, initial_capital=100000.0):
        """
        Inizializza il portfolio con la coda delle barre e degli eventi.
        Include anche un indice datetime iniziale e un capitale iniziale
        (USD se non diversamente specificato).

        Parametri:
        bars - L'oggetto DataHandler con i dati di mercato correnti.
        events: l'oggetto Event Queue (coda di eventi).
        start_date - La data di inizio (barra) del portfolio.
        initial_capital - Il capitale iniziale in USD.
        """
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start_date = start_date
        self.initial_capital = initial_capital

        self.all_positions = self.construct_all_positions()
        self.current_positions = dict((k, v) for k, v in [(s, 0) for s in self.symbol_list])

        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()


    def construct_all_positions(self):
        """
        Costruisce l'elenco delle posizioni utilizzando start_date
        per determinare quando inizierà l'indice temporale.
        """
        d = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        d['datetime'] = self.start_date
        return [d]


    def construct_all_holdings(self):
        """
        Costruisce l'elenco delle partecipazioni utilizzando start_date
        per determinare quando inizierà l'indice temporale.
        """
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        d['datetime'] = self.start_date
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return [d]


    def construct_current_holdings(self):
        """
        Questo costruisce il dizionario che conterrà l'istantaneo
        valore del portafoglio attraverso tutti i simboli.
        """
        d = dict( (k,v) for k, v in [(s, 0.0) for s in self.symbol_list] )
        d['cash'] = self.initial_capital
        d['commission'] = 0.0
        d['total'] = self.initial_capital
        return d


    def update_timeindex(self, event):
        """
        Aggiunge un nuovo record alla matrice delle posizioni per la barra corrente
        dei dati di mercato. Questo riflette la barra PRECEDENTE, cioè in questa fase
        tutti gli attuali dati di mercato sono noti (OLHCVI).

        Utilizza un MarketEvent dalla coda degli eventi.
        """
        latest_datetime = self.bars.get_latest_bar_datetime(
                                self.symbol_list[0]
                            )

        # Update positions
        dp = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        dp['datetime'] = latest_datetime

        for s in self.symbol_list:
            dp[s] = self.current_positions[s]

        # Aggiunge le posizioni correnti
        self.all_positions.append(dp)

        # Aggiorno delle holdings
        dh = dict( (k,v) for k, v in [(s, 0) for s in self.symbol_list] )
        dh['datetime'] = latest_datetime
        dh['cash'] = self.current_holdings['cash']
        dh['commission'] = self.current_holdings['commission']
        dh['total'] = self.current_holdings['cash']

        for s in self.symbol_list:
            # Approossimazione ad un valore reale
            market_value = self.current_positions[s] * \
                            self.bars.get_latest_bar_value(s, "adj_close")
            dh[s] = market_value
            dh['total'] += market_value

        # Aggiunta alle holdings correnti
        self.all_holdings.append(dh)


    def update_positions_from_fill(self, fill):
        """
        Prende un oggetto FilltEvent e aggiorna la matrice delle posizioni
        per riflettere le nuove posizioni.

        Parametri:
        fill - L'oggetto FillEvent da aggiornare con le posizioni.
        """
        # Check whether the fill is a buy or sell
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == 'SELL':
            fill_dir = -1

        # Aggiorna le posizioni con le nuove quantità
        self.current_positions[fill.symbol] += fill_dir * fill.quantity


    def update_holdings_from_fill(self, fill):
        """
        Prende un oggetto FillEvent e aggiorna la matrice delle holdings
        per riflettere il valore delle holdings.

        Parametri:
        fill - L'oggetto FillEvent da aggiornare con le holdings.
        """
        # Controllo se l'oggetto fill è un buy o sell
        fill_dir = 0
        if fill.direction == 'BUY':
            fill_dir = 1
        if fill.direction == 'SELL':
            fill_dir = -1

        # Aggiorna la lista di holdings con le nuove quantità
        fill_cost = self.bars.get_latest_bar_value(fill.symbol, "adj_close")  # Close price
        cost = fill_dir * fill_cost * fill.quantity
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= (cost + fill.commission)
        self.current_holdings['total'] -= (cost + fill.commission)


    def update_fill(self, event):
        """
        Aggiorna le attuali posizioni e holdings del portafoglio da un FillEvent.
        """
        if event.type == 'FILL':
            self.update_positions_from_fill(event)
            self.update_holdings_from_fill(event)


    def generate_naive_order(self, signal):
        """
        Trasmette semplicemente un oggetto OrderEvent con una quantità costante
        che dipendente dell'oggetto segnale, senza gestione del rischio o
        considerazioni sul dimensionamento della posizione.

        Parametri:
        signal - L'oggetto SignalEvent.
        """
        order = None

        symbol = signal.symbol
        direction = signal.signal_type
        strength = signal.strength

        mkt_quantity = floor(100 * strength)
        cur_quantity = self.current_positions[symbol]
        order_type = 'MKT'

        if direction == 'LONG' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'BUY')
        if direction == 'SHORT' and cur_quantity == 0:
            order = OrderEvent(symbol, order_type, mkt_quantity, 'SELL')

        if direction == 'EXIT' and cur_quantity > 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'SELL')
        if direction == 'EXIT' and cur_quantity < 0:
            order = OrderEvent(symbol, order_type, abs(cur_quantity), 'BUY')
        return order


    def update_signal(self, event):
        """
        Azioni a seguito di un SignalEvent per generare nuovi ordini
        basati sulla logica del portafoglio
        """
        if event.type == 'SIGNAL':
            order_event = self.generate_naive_order(event)
            self.events.put(order_event)


    def create_equity_curve_dataframe(self):
        """
        Crea un DataFrame pandas dalla lista di dizionari "all_holdings"
        """
        curve = pd.DataFrame(self.all_holdings)
        curve.set_index('datetime', inplace=True)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0+curve['returns']).cumprod()
        self.equity_curve = curve


    def output_summary_stats(self):
        """
        Crea un elenco di statistiche di riepilogo per il portafoglio
        come lo Sharpe Ratio e le informazioni sul drowdown.
        """
        total_return = self.equity_curve['equity_curve'][-1]
        returns = self.equity_curve['returns']
        pnl = self.equity_curve['equity_curve']
        sharpe_ratio = create_sharpe_ratio(returns)
        drawdown, max_dd, dd_duration = create_drawdowns(pnl)
        self.equity_curve['drawdown'] = drawdown
        stats = [("Total Return", "%0.2f%%" % \
                  ((total_return - 1.0) * 100.0)),
                 ("Sharpe Ratio", "%0.2f" % sharpe_ratio),
                 ("Max Drawdown", "%0.2f%%" % (max_dd * 100.0)),
                 ("Drawdown Duration", "%d" % dd_duration)]
        self.equity_curve.to_csv('equity.csv')
        return stats