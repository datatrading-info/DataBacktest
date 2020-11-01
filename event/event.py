
# codice python relativo all'articolo presente su datatrading.info
# https://datatrading.info/motore-di-backtesting-con-python-parte-ii-gli-eventi/

# event.py

class Event(object):
    """
    Event è la classe base che fornisce un'interfaccia per tutti
    i tipi di sottoeventi (ereditati), che attiverà ulteriori
    eventi nell'infrastruttura di trading.
    """
    pass



class MarketEvent(Event):
    """
    Gestisce l'evento di ricezione di un nuovo aggiornamento dei
    dati di mercato con le corrispondenti barre.
    """

    def __init__(self):
        """
        Inizializzazione del MarketEvent.
        """
        self.type = 'MARKET'




class SignalEvent(Event):
    """
    Gestisce l'evento di invio di un Segnale da un oggetto Strategia.
    Questo viene ricevuto da un oggetto Portfolio e si agisce su di esso.
    """

    def __init__(self, strategy_id, symbol, datetime, signal_type, strength):
        """
        Inizializzazione del SignalEvent.

        Parametri:
        symbol - Il simbolo del ticker, es. 'GOOG'.
        datetime - Il timestamp al quale il segnale è stato generato.
        signal_type - 'LONG' o 'SHORT'.
        """

        self.type = 'SIGNAL'
        self.strategy_id = strategy_id
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type
        self.strength = strength




class OrderEvent(Event):
    """
    Gestisce l'evento di invio di un ordine al sistema di esecuzione.
    L'ordine contiene un simbolo (ad esempio GOOG), un tipo di ordine
    (a mercato o limite), una quantità e una direzione.
    """

    def __init__(self, symbol, order_type, quantity, direction):
        """
        Inizializza il tipo di ordine, impostando se è un ordine a mercato
        ('MKT') o un ordine limite ('LMT'), la quantità (integral)
        e la sua direzione ('BUY' or 'SELL').

        Parametri:
        symbol - Lo strumento da tradare.
        order_type - 'MKT' o 'LMT' per ordine Market or Limit.
        quantity - Intero non negativo per la quantità.
        direction - 'BUY' o 'SELL' per long o short.
        """

        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction

    def print_order(self):
        """
        Stampa dei valori che compongono l'ordine.
        """
        print
        "Order: Symbol=%s, Type=%s, Quantity=%s, Direction=%s" % \
        (self.symbol, self.order_type, self.quantity, self.direction)




class FillEvent(Event):
    """
    Incorpora il concetto di un ordine eseguito, come restituito
    da un broker. Memorizza l'effettiva quantità scambiata di
    uno strumento e a quale prezzo. Inoltre, memorizza
    la commissione del trade applicata dal broker.
    """

    def __init__(self, timeindex, symbol, exchange, quantity,
                 direction, fill_cost, commission=None):
        """
        Inizializza l'oggetto FillEvent. Imposta il simbolo, il broker,
        la quantità, la direzione, il costo di esecuzione e una
        commissione opzionale.

        Se la commissione non viene fornita, l'oggetto Fill la calcola
        in base alla dimensione del trade e alle commissioni di
        Interactive Brokers.

        Parametri:
        timeindex - La risoluzione delle barre quando l'ordine è stato eseguito.
        symbol - Lo strumento che è stato eseguito.
        exchange - Il broker/exchange dove l'ordine è stato eseguito.
        quantity - La quantità effettivamente scambiata.
        direction - La direzione dell'esecuzione ('BUY' o 'SELL')
        fill_cost - Il valore nominale in dollari.
        commission - La commissione opzionale inviata da IB.
        """

        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost

        # Calcolo della commissione
        if commission is None:
            self.commission = self.calculate_ib_commission()
        else:
            self.commission = commission

    def calculate_ib_commission(self):
        """
        Calcolo delle commisioni di trading basate sulla struttura
        delle fee per la API di Interactive Brokers, in USD.

        Non sono incluse le fee di exchange o ECN.

        Basata sulla "US API Directed Orders":
        https://www.interactivebrokers.com/en/index.php?f=commission&p=stocks2
        """
        full_cost = 1.3
        if self.quantity <= 500:
            full_cost = max(1.3, 0.013 * self.quantity)
        else:  # Greater than 500
            full_cost = max(1.3, 0.008 * self.quantity)
        return full_cost
        """
        if self.quantity <= 300:
            full_cost = max(0.35, 0.0035 * self.quantity)
        elif self.quantity <= 3000:
            full_cost = max(0.35, 0.002 * self.quantity)
        elif self.quantity <= 20000:
            full_cost = max(0.35, 0.0015 * self.quantity)
        elif self.quantity <= 100000:
            full_cost = max(0.35, 0.001 * self.quantity)
        else:  # Maggiore di 100 mila azioni
            full_cost = max(0.35, 0.0005 * self.quantity)
   #     full_cost = min(full_cost, 1.0 / 100.0 * self.quantity * self.fill_cost)
        """
        return full_cost