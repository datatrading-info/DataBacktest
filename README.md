# DataBacktest
Framework per un approccio più realistico alla simulazione della strategia di trading, usando Python per costruire un ambiente di backtesting basato sugli eventi.
## www.datatrading.info

### Perchè abbiamo bisogno di un Backtesting Event-Driven
I sistemi basati sugli eventi offrono molti vantaggi rispetto a un approccio vettorializzato:

Riutilizzo del codice – un backtester basato sugli eventi, in base alla progettazione, può essere utilizzato sia per il backtesting storico sia per il live trading con una minima modifica dei componenti. Questo non è possibile per i backtesting vettorizzati dove tutti i dati devono essere disponibili contemporaneamente per poter effettuare analisi statistiche.
Bias di Look-Ahead – con un backtesting basato sugli eventi non vi è alcun bias di previsione perché l’acquisizione dei dati finanziari è gestita come un “evento” su cui si deve effettuare specifiche azioni. In questo modo è possibile un ambiente di backtestering event-driven è alimentato  “instante dopo instante” con i dati di mercato, replicando il comportamento di un sistema di gestione degli ordini e del portafoglio.
Realismo – I backtesting basati sugli eventi consentono una significativa personalizzazione del modalità di esecuzione degli ordini e dei costi di transazione sostenuti. È semplice gestire il market-order e il limit-order, oltre al market-on-open (MOO) e al market-on-close (MOC), poiché è possibile costruire un gestore di exchange personalizzato.
 

Sebbene i sistemi basati sugli eventi siano dotati di numerosi vantaggi, essi presentano due importanti svantaggi rispetto ai più semplici sistemi vettorizzati. Innanzitutto sono molto più complessi da implementare e testare. Ci sono più “parti mobili” che causano una maggiore probabilità di introdurre bug. Per mitigare questa criticità è possibile implementare una  metodologia di testing del software, come il test-driven development.

In secondo luogo, hanno tempi di esecuzione più lenti da eseguire rispetto a un sistema vettorializzato. Le operazioni vettoriali ottimizzate non possono essere utilizzate quando si eseguono calcoli matematici. Discuteremo dei modi per superare queste limitazioni negli articoli successivi.

### Struttura di un sistema di Backtesting Event-Driven
Per applicare un approccio event-driven a un sistema di backtesting è necessario definire i componenti base (o oggetti) che gestiscono compiti specifici:

Event: l’Event è la classe fondamentale di un sistema event-driven. Contiene un attributto “tipo” (ad esempo, “MARKET”, “SIGNAL”, “ORDER” o “FILL”) che determina come viene gestito uno specifico evento all’interno dell’event-loop.<br>
Event Queue: la Coda degli Eventi è un oggetto Python Queue che memorizza tutti gli oggetti della sotto-classe Event generati dal resto del software.<br>
DataHandler: il DataHandler è una classe base astratta (ABC) che presenta un’interfaccia per la gestione di dati storici o del mercato in tempo reale. Fornisce una significativa flessibilità in quanto i moduli della strategia e del portfolio possono essere riutilizzati da entrambi gli approcci. Il DataHandler genera un nuovo MarketEvent ad loop del sistema (vedi sotto).<br>
Strategy: anche la Strategy è una classe ABC e presenta un’interfaccia per elaborare i dati di mercato e generare i corrispondenti SignalEvents, che vengono infine utilizzati dall’oggetto Portfolio. Un SignalEvent contiene un simbolo ticker, una direzione (LONG or SHORT) e un timestamp.<br>
Portfolio: si tratta di una classe ABC che implementa la gestione degli ordini associata alle posizioni attuali e future di una strategia. Svolge anche la gestione del rischio in tutto il portafoglio, compresa l’esposizione settoriale e il dimensionamento delle posizioni. In un’implementazione più sofisticata, questo potrebbe essere delegato a una classe RiskManagement. La classe Portfolio prende un SignalEvents dalla coda e genera uno o più OrderEvents che vengono aggiunti alla coda.<br>
ExecutionHandler: l’ExecutionHandler simula una connessione a una società di intermediazione o broker. Il suo compito consiste nel prelevare gli OrderEvents dalla coda ed eseguirli, tramite un approccio simulato o una connessione reale verso il broker. Una volta eseguiti gli ordini, il gestore crea i FillEvents, che descrivono ciò che è stato effettivamente scambiato, comprese le commissioni, lo spread e lo slippage (se modellato).<br>
Loop – Tutti questi componenti sono racchiusi in un event-loop che gestisce correttamente tutti i tipi di eventi, indirizzandoli al componente appropriato.<br><br>
Questo è il modello base di un motore di trading. Vi è un significativo margine di espansione, in particolare per quanto riguarda l’utilizzo del portafoglio. Inoltre, i diversi modelli di costo delle transazioni possono essere implementati utilizzando una propria gerarchia di classi. In questa fase però introdurrebbe una complessità inutile all’interno di questa serie di articoli, quindi al momento non viene approfondita ulteriormente. 

