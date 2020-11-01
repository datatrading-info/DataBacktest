
# codice python relativo all'articolo presente su datatrading.info
# https://datatrading.info/motore-di-backtesting-con-python-parte-iv-gestione-della-strategia/

# strategy.py

import datetime
import numpy as np
import pandas as pd
import queue

from abc import ABCMeta, abstractmethod

from event.event import SignalEvent


class Strategy(object):
    """
    Strategy è una classe base astratta che fornisce un'interfaccia per
    tutti i successivi oggetti (ereditati) di gestione della strategia.

    L'obiettivo di un oggetto (derivato da) Strategy è generare un oggetto
    Signal per specifici simboli basati sugli input di Bars
    (OLHCVI) generati da un oggetto DataHandler.

    Questo è progettato per funzionare sia con dati storici che in tempo reale
    quindi l'oggetto Strategy è agnostico rispetto all'origine dati,
    poiché ricava le tuple di barre da un oggetto Queue (coda).
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def calculate_signals(self):
        """
        Fornisce il meccanismo per calcolare la lista di segnali.
        """
        raise NotImplementedError("Should implement calculate_signals()")



class BuyAndHoldStrategy(Strategy):
    """
    Questa è una strategia estremamente semplice che va LONG su tutti
    i simboli non appena viene ricevuta una barra. Non uscirà mai da una posizione.

    Viene utilizzato principalmente come meccanismo di test per la classe Strategy
    nonché un benchmark con cui confrontare le altre strategie.
    """

    def __init__(self, bars, events):
        """
        Inizializza la strategia "buy and hold".

        Parametri:
        bars - L'oggetto DataHandler che fornisce le informazioni sui prezzi
        events - L'oggetto Event Queue (coda di eventi).
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events

        # Quando il segnale "buy & hold" viene inviato, questi sono impostati a True
        self.bought = self._calculate_initial_bought()


    def _calculate_initial_bought(self):
        """
        Aggiunge le chiavi di tutti i simboli al dizionario "bought"
        e li imposta su False.
        """
        bought = {}
        for s in self.symbol_list:
            bought[s] = False
        return bought


    def calculate_signals(self, event):
        """
        For "Buy and Hold" generiamo un singolo segnale per simbolo
        e quindi nessun segnale aggiuntivo. Ciò significa che siamo
        costantemente LONG sul mercato a partire dalla data di
        inizializzazione della strategia.

        Parametri
        event - Un oggetto MarketEvent.
        """
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars(s, N=1)
                if bars is not None and bars != []:
                    if self.bought[s] == False:
                        # (Symbol, Datetime, Type = LONG, SHORT or EXIT)
                        signal = SignalEvent(bars[0][0], bars[0][1], 'LONG')
                        self.events.put(signal)
                        self.bought[s] = True