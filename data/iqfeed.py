# iqfeed.py

import sys
import socket


def read_historical_data_socket(sock, recv_buffer=4096):
    """
    Lettura delle informazioni dal socket, in un buffer
    su misura, ricevendo solo 4096 byte alla volta.

    Parametri:
    sock - L'oggetto socket
    recv_buffer - Quantità in byte da ricevere per lettura
        """
    ibuffer = ""
    data = ""
    while True:
        data = sock.recv(recv_buffer)
        ibuffer += data

        # Controllo se è arrivata la stringa di fine messaggio
        if "!ENDMSG!" in ibuffer:
            break

    # Rimuovere la stringa di fine messaggio
    ibuffer = ibuffer[:-12]
    return ibuffer



if __name__ == "__main__":
    # Definizione dell'host del server, la porta e il simbolo da scaricare
    host = "127.0.0.1"  # Localhost
    port = 9100  # porta del socket per i dati storici
    syms = ["SPY", "AAPL", "GOOG", "AMZN"]

    # Download ogni simbolo su disco
    for sym in syms:
        print("Downloading symbol: %s..." % sym)

        # Costruzione del messaggio previsto da IQFeed per ricevere i dati
        message = "HIT,%s,60,20140101 075000,,,093000,160000,1\n" % sym

        # Apertura di un socket streaming localmente verso un server IQFeed
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))

        # Invia i messaggi per le richieste di dati
        # storici e immagazziona i dati
        sock.sendall(message)
        data = read_historical_data_socket(sock)
        sock.close

        # Rimuovere tutte le linee finali e le virgole di fine
        # linea che delimitano ogni record
        data = "".join(data.split("\r"))
        data = data.replace(",\n","\n")[:-1]

        # Scrive il flusso dei deti sul disco
        f = open("%s.csv" % sym, "w")
        f.write(data)
        f.close()