import html
import pprint
import re
from html.parser import HTMLParser
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import confusion_matrix


class ReutersParser(HTMLParser):
    """
    ReutersParser è una sottoclasse HTMLParser e viene utilizzato per aprire file SGML
    associati al dataset di Reuters-21578.

    Il parser è un generatore e produrrà un singolo documento alla volta.
    Poiché i dati verranno suddivisi in blocchi durante l'analisi, è necessario mantenere
    alcuni stati interni di quando i tag sono stati "inseriti" e "eliminati".
    Da qui le variabili booleani in_body, in_topics e in_topic_d.
    """

    def __init__(self, encoding='latin-1'):
        """
        Inizializzo la superclasse (HTMLParser) e imposto il parser.
        Imposto la decodifica dei file SGML con latin-1 come default.
        """
        html.parser.HTMLParser.__init__(self)
        self._reset()
        self.encoding = encoding

    def _reset(self):
        """
        Viene chiamata solo durante l'inizializzazione della classe parser
        e quando è stata generata una nuova tupla topic-body. Si
        resetta tutto lo stato in modo che una nuova tupla possa essere
        successivamente generato.
        """
        self.in_body = False
        self.in_topics = False
        self.in_topic_d = False
        self.body = ""
        self.topics = []
        self.topic_d = ""

    def parse(self, fd):
        """
        parse accetta un descrittore di file e carica i dati in blocchi
        per ridurre al minimo l'utilizzo della memoria.
        Quindi produce nuovi documenti man mano che vengono analizzati.
        """
        self.docs = []
        for chunk in fd:
            self.feed(chunk.decode(self.encoding))
            for doc in self.docs:
                yield doc
            self.docs = []
        self.close()

    def handle_starttag(self, tag, attrs):
        """
        Questo metodo viene utilizzato per determinare cosa fare quando
        il parser incontra un particolare tag di tipo "tag".
        In questo caso, impostiamo semplicemente i valori booleani
        interni su True se è stato trovato quel particolare tag.
        """
        if tag == "reuters":
            pass
        elif tag == "body":
            self.in_body = True
        elif tag == "topics":
            self.in_topics = True
        elif tag == "d":
            self.in_topic_d = True

    def handle_endtag(self, tag):
        """
        Questo metodo viene utilizzato per determinare cosa fare
        quando il parser termina con un particolare tag di tipo "tag".

        Se il tag è un tag <REUTERS>, rimuoviamo tutti gli spazi bianchi
        con un'espressione regolare e quindi aggiungiamo la tupla topic-body.

        Se il tag è un tag <BODY> o <TOPICS>, impostiamo semplicemente lo
        stato interno su False per questi valori booleani, rispettivamente.

        Se il tag è un tag <D> (che si trova all'interno di un tag <TOPICS>),
        aggiungiamo l'argomento specifico all'elenco "topics" e infine lo resettiamo.
        """
        if tag == "reuters":
            self.body = re.sub(r'\s+', r' ', self.body)
            self.docs.append((self.topics, self.body))
            self._reset()
        elif tag == "body":
            self.in_body = False
        elif tag == "topics":
            self.in_topics = False
        elif tag == "d":
            self.in_topic_d = False
            self.topics.append(self.topic_d)
            self.topic_d = ""

    def handle_data(self, data):
        """
        I dati vengono semplicemente aggiunti allo stato appropriato
        per quel particolare tag, fino a quando non viene visualizzato
        il tag di chiusura finale.
        """
        if self.in_body:
            self.body += data
        elif self.in_topic_d:
            self.topic_d += data


def obtain_topic_tags():
    """
    Apre il file dell'elenco degli argomenti e importa tutti i nomi
    degli argomenti facendo attenzione a rimuovere il finale "\ n" da ogni parola.
    """
    topics = open(
        "data/all-topics-strings.lc.txt", "r"
    ).readlines()
    topics = [t.strip() for t in topics]
    return topics


def filter_doc_list_through_topics(topics, docs):
    """
    Legge tutti i documenti e crea un nuovo elenco di due tuple che
    contengono una singola voce di funzionalità e il corpo del testo,
    invece di un elenco di argomenti. Rimuove tutte le caratteristiche
    geografiche e conserva solo quei documenti che hanno almeno un
    argomento non geografico.
    """
    ref_docs = []
    for d in docs:
        if d[0] == [] or d[0] == "":
            continue
        for t in d[0]:
            if t in topics:
                d_tup = (t, d[1])
                ref_docs.append(d_tup)
                break
    return ref_docs


def create_tfidf_training_data(docs):
    """
    Crea un elenco di corpus di documenti (rimuovendo le etichette della classe),
    quindi applica la trasformazione TF-IDF a questo elenco.

   La funzione restituisce sia il vettore etichetta di classe (y) che
   la matrice token / feature corpus (X).
    """
    # Crea le classi di etichette per i dati di addestramento
    y = [d[0] for d in docs]

    # Crea la lista dei corpus del documenti
    corpus = [d[1] for d in docs]

    # Create la vettorizzazione TF-IDF e trasforma il corpus
    vectorizer = TfidfVectorizer(min_df=1)
    X = vectorizer.fit_transform(corpus)
    return X, y



def train_svm(X, y):
    """
    Crea e addestra la Support Vector Machine.
    """
    svm = SVC(C=1000000.0, gamma=0.0, kernel='rbf')
    svm.fit(X, y)
    return svm


if __name__ == "__main__":
    # Apre il primo set di dati Reuters e crea il parser
    filename = "data/reut2-000.sgm"
    parser = ReutersParser()

    # Analizza il documento e forza tutti i documenti generati
    # in un elenco in modo che possano essere stampati sulla console
    docs = list(parser.parse(open(filename, 'rb')))




if __name__ == "__main__":
    # Apre il primo set di dati Reuters e crea il parser
    files = ["data/reut2-%03d.sgm" % r for r in range(0, 22)]
    parser = ReutersParser()

    # Analizza il documento e forza tutti i documenti generati
    # in un elenco in modo che possano essere stampati sulla console
    docs = []
    for fn in files:
        for d in parser.parse(open(fn, 'rb')):
            docs.append(d)
    # Ottenere i tags e filtrare il documento con essi
    topics = obtain_topic_tags()
    ref_docs = filter_doc_list_through_topics(topics, docs)

    # Vettorizzazione e TF-IDF
    X, y = create_tfidf_training_data(ref_docs)

    # Crea il training-test split dei dati
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )


    # Crea ed addestra la Support Vector Machine
    svm = train_svm(X_train, y_train)

    # Crea un array delle predizioni con i dati di test
    pred = svm.predict(X_test)

    # Calcolo del hit-rate e della confusion matrix per ogni modello
    print(svm.score(X_test, y_test))
    print(confusion_matrix(pred, y_test))

