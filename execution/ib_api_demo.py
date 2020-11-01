# https://datatrading.info/come-creare-un-account-demo-su-interactive-brokers/

# ib_api_demo.py

from ib.ext.Contract import Contract
from ib.ext.Order import Order
from ib.opt import Connection, message


def error_handler(msg):
    """Gestione per la cattura dei messagi di errori"""
    print("Server Error: %s" % msg)

def reply_handler(msg):
    """Gestione delle risposte dal server"""
    print("Server Response: %s, %s" % (msg.typeName, msg))

def create_contract(symbol, sec_type, exch, prim_exch, curr):
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

def create_order(order_type, quantity, action):
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


if __name__ == "__main__":
    # Collegarsi alla Trader Workstation (TWS) in esecuzione
    # sulla solita porta 7496, con un clientId di 100
    # (Il clientId è scelto da noi e avremo bisogno di
    # ID separati sia per la connessione di esecuzione che per
    # connessione dati di mercato)
    tws_conn = Connection.create(port=7496, clientId=100)
    tws_conn.connect()

    # Assegna la funzione di gestione degli errori definita
    # sopra alla connessione TWS
    tws_conn.register(error_handler, 'Error')

    # Assegna tutti i messaggi di risposta del server alla
    # funzione reply_handler definita sopra
    tws_conn.registerAll(reply_handler)

    # Crea un ordine ID che sia "globale" per questa sessione. Questo
    # dovrà essere incrementato una volta inviati nuovi ordini.
    order_id = 1

    # Crea un contratto in stock GOOG tramite il routing degli ordini SMART
    goog_contract = create_contract('GOOG', 'STK', 'SMART', 'SMART', 'USD')

    # si va long di 100 azioni di Google
    goog_order = create_order('MKT', 100, 'BUY')

    # Uso della connessione per inviare l'ordine a IB
    tws_conn.placeOrder(order_id, goog_contract, goog_order)

    # Disconnessione da TWS
    tws_conn.disconnect()