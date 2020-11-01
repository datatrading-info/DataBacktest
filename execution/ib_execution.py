
# codice python relativo all'articolo presente su datatrading.info
# https://datatrading.info/motore-di-backtesting-con-python-parte-ix-connessione-con-ib/

# ib_execution.py

import datetime
import time

from ib.ext.Contract import Contract
from ib.ext.Order import Order
from ib.opt import ibConnection, message

from event.event import FillEvent, OrderEvent
from execution.execution import ExecutionHandler


class IBExecutionHandler(ExecutionHandler):
    """
    Gestisce l'esecuzione degli ordini tramite l'API di Interactive
    Brokers, da utilizzare direttamente sui conti reali durante il
    live trading.
    """

    def __init__(self, events,
                 order_routing="SMART",
                 currency="USD"):
        """
        Inizializza l'instanza di IBExecutionHandler.
        """
        self.events = events
        self.order_routing = order_routing
        self.currency = currency
        self.fill_dict = {}

        self.tws_conn = self.create_tws_connection()
        self.order_id = self.create_initial_order_id()
        self.register_handlers()


    def _error_handler(self, msg):
        """
        Gestore per la cattura dei messagi di errori
        """
        # Al momento non c'è gestione degli errori.
        print
        "Server Error: %s" % msg


    def _reply_handler(self, msg):
        """
        Gestione delle risposte dal server
        """
        # Gestisce il processo degli orderId degli ordini aperti
        if msg.typeName == "openOrder" and \
                msg.orderId == self.order_id and \
                not self.fill_dict.has_key(msg.orderId):
            self.create_fill_dict_entry(msg)
        # Gestione dell'esecuzione degli ordini (Fills)
        if msg.typeName == "orderStatus" and \
                msg.status == "Filled" and \
                self.fill_dict[msg.orderId]["filled"] == False:
            self.create_fill(msg)
        print
        "Server Response: %s, %s\n" % (msg.typeName, msg)



    def create_tws_connection(self):
        """
        Collegamento alla Trader Workstation (TWS) in esecuzione
        sulla porta standard 7496, con un clientId di 10.
        Il clientId è scelto da noi e avremo bisogno ID separati
        sia per la connessione di esecuzione che per la connessione
        ai dati di mercato, se quest'ultima è utilizzata altrove.
        """
        tws_conn = ibConnection()
        tws_conn.connect()
        return tws_conn


    def create_initial_order_id(self):
        """
        Crea l'iniziale ID dell'ordine utilizzato da Interactive
        Broker per tenere traccia degli ordini inviati.
        """
        # Qui c'è spazio per una maggiore logica, ma
        # per ora useremo "1" come predefinito.
        return 1


    def register_handlers(self):
        """
        Registra le funzioni di gestione di errori e dei
        messaggi di risposta dal server.
        """
        # Assegna la funzione di gestione degli errori definita
        # sopra alla connessione TWS
        self.tws_conn.register(self._error_handler, 'Error')

        # Assegna tutti i messaggi di risposta del server alla
        # funzione reply_handler definita sopra
        self.tws_conn.registerAll(self._reply_handler)


    def create_contract(self, symbol, sec_type, exch, prim_exch, curr):
        """
        Crea un oggetto Contract definendo cosa sarà
        acquistato, in quale exchange e in quale valuta.

        symbol - Il simbolo del ticker per il contratto
        sec_type - Il tipo di asset per il contratto ("STK" è "stock")
        exch - La borsa su cui eseguire il contratto
        prim_exch - Lo scambio principale su cui eseguire il contratto
        curr - La valuta in cui acquistare il contratto
        """
        contract = Contract()
        contract.m_symbol = symbol
        contract.m_secType = sec_type
        contract.m_exchange = exch
        contract.m_primaryExch = prim_exch
        contract.m_currency = curr
        return contract


    def create_order(self, order_type, quantity, action):
        """
        Crea un oggetto Ordine (Market/Limit) per andare long/short.

        order_type - "MKT", "LMT" per ordini a mercato o limite
        quantity - Numero intero di asset dell'ordine
        action - 'BUY' o 'SELL'
        """
        order = Order()
        order.m_orderType = order_type
        order.m_totalQuantity = quantity
        order.m_action = action
        return order


    def create_fill_dict_entry(self, msg):
        """
        Crea una voce nel dizionario Fill che elenca gli orderIds
        e fornisce informazioni sull'asset. Ciò è necessario
        per il comportamento guidato dagli eventi del gestore
        dei messaggi del server IB.
        """
        self.fill_dict[msg.orderId] = {
            "symbol": msg.contract.m_symbol,
            "exchange": msg.contract.m_exchange,
            "direction": msg.order.m_action,
            "filled": False
        }

    # ib_execution.py

    def create_fill(self, msg):
        """
        Gestisce la creazione del FillEvent che saranno
        inseriti nella coda degli eventi successivamente
        alla completa esecuzione di un ordine.
        """
        fd = self.fill_dict[msg.orderId]

        # Preparazione dei dati di esecuzione
        symbol = fd["symbol"]
        exchange = fd["exchange"]
        filled = msg.filled
        direction = fd["direction"]
        fill_cost = msg.avgFillPrice

        # Crea un oggetto di Fill Event
        fill_event = FillEvent(
            datetime.datetime.utcnow(), symbol,
            exchange, filled, direction, fill_cost
        )

        # Controllo per evitare che messaggi multipli non
        # creino dati addizionali.
        self.fill_dict[msg.orderId]["filled"] = True

        # Inserisce il fill event nella coda di eventi
        self.events.put(fill_event)


    def execute_order(self, event):
        """
        Crea il necessario oggetto ordine InteractiveBrokers
        e lo invia a IB tramite la loro API.

        I risultati vengono quindi interrogati per generare il
        corrispondente oggetto Fill, che viene nuovamente posizionato
        nella coda degli eventi.

        Parametri:
        event - Contiene un oggetto Event con informazioni sull'ordine.
        """
        if event.type == 'ORDER':
            # Prepara i parametri per l'ordine dell'asset
            asset = event.symbol
            asset_type = "STK"
            order_type = event.order_type
            quantity = event.quantity
            direction = event.direction

            # Crea un contratto per Interactive Brokers tramite
            # l'evento Order in inuput
            ib_contract = self.create_contract(
                asset, asset_type, self.order_routing,
                self.order_routing, self.currency
            )

            # Crea un ordine per Interactive Brokers tramite
            # l'evento Order in inuput
            ib_order = self.create_order(
                order_type, quantity, direction
            )

            # Usa la connessione per inviare l'ordine a IB
            self.tws_conn.placeOrder(
                self.order_id, ib_contract, ib_order
            )

            # NOTE: questa linea è cruciale
            # Questo assicura che l'ordina sia effettivamente trasmesso!
            time.sleep(1)

            # Incrementa l'ordene ID per questa sessione
            self.order_id += 1