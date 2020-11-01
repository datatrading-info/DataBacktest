
# codice python relativo all'articolo presente su datatrading.info
# https://datatrading.info/motore-di-backtesting-con-python-parte-vi-esecuzione-degli-ordini/

# execution.py

import datetime
import queue

from abc import ABCMeta, abstractmethod

from event.event import FillEvent, OrderEvent


class ExecutionHandler(object):
    """
    La classe astratta ExecutionHandler gestisce l'interazione
    tra un insieme di oggetti "ordini" generati da un portafoglio e
    l'ultimo set di oggetti Fill che effettivamente si verificano
    nel mercato.

    Gli handles possono essere utilizzati per creare sottoclassi
    con interfacce identiche per broker simulati o broker live.
    Questo permette di sottoporre strategie a backtesting in modo
    molto simile al motore di live trading.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def execute_order(self, event):
        """
        Accetta un evento Order e lo esegue, producendo
        un evento Fill che viene inserito nella coda degli eventi.

        Parametri:
        event - Contiene un oggetto Event con informazioni sull'ordine.
        """
        raise NotImplementedError("Should implement execute_order()")


class SimulatedExecutionHandler(ExecutionHandler):
    """
    Il gestore di esecuzione simulato converte semplicemente tutti gli
    oggetti Ordine automaticamente negli equivalenti oggetti Fill
    senza considerare i problemi di latenza, slittamento e rapporto di
    esecuzione (fill-ratio).

    Ciò consente un semplice test "first go" di qualsiasi strategia,
    prima dell'implementazione con un gestiore di esecuzione più sofisticato.
    """

    def __init__(self, events):
        """
        Inizializza il gestore, impostando internamente le code degli eventi.

        Parametri
        events - L'oggetto di coda degli eventi.
        """
        self.events = events

    def execute_order(self, event):
        """
        Converte semplicemente gli oggetti Order in oggetti Fill base,
        cioè senza considerare latenza, slittamento o rapporto di esecuzione.

        Parametri:
        event - Contiene un oggetto Event con informazioni sull'ordine.
        """
        if event.type == 'ORDER':
            fill_event = FillEvent(datetime.datetime.utcnow(), event.symbol,
                                   'ARCA', event.quantity, event.direction, None)
            self.events.put(fill_event)