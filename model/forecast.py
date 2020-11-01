#!/usr/bin/python
# -*- coding: utf-8 -*-
# forecast.py

# codice python relativo all'articolo presente su datatrading.info
# https://datatrading.info/introduzione-al-forecasting-delle-serie-temporali-finanziare-2/

import datetime
import numpy as np
import pandas as pd

import pandas_datareader as pdr
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
from sklearn.metrics import confusion_matrix
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis as QDA
from sklearn.svm import LinearSVC, SVC

def create_lagged_series(symbol, start_date, end_date, lags=5):
    """
    Questo crea un DataFrame Pandas che memorizza i rendimenti percentuali
    del prezzo di chiusura aggiustato delle barre di un titolo azionario scaricate
    da Yahoo Finance, e memorizza una serie di rendimenti ritardati dai giorni di
    negoziazione precedenti (il valore di ritardo predefinito è di 5 giorni).
    Sono inclusi anche i volume degli scambi, e la direzione del giorno precedente.
    """

    # Download dei ddti sulle azioni da Yahoo Finance
    ts = pdr.DataReader(
          symbol, "yahoo",
          start_date-datetime.timedelta(days=365),
          end_date
         )

    # Crea un nuovo DataFrame dei dati ritardati
    tslag = pd.DataFrame(index=ts.index)
    tslag["Today"] = ts["Adj Close"]
    tslag["Volume"] = ts["Volume"]

    # Crea una serie ritardata dei precendenti prezzi di chiusura dei periodi di trading
    for i in range(0, lags):
        tslag["Lag%s" % str(i+1)] = ts["Adj Close"].shift(i+1)

    # Crea il Dataframe dei rendimenti
    tsret = pd.DataFrame(index=tslag.index)
    tsret["Volume"] = tslag["Volume"]
    tsret["Today"] = tslag["Today"].pct_change()*100.0

    # Se qualsiasi dei valori dei rendimenti percentuali è pari a zero, si imposta questi con
    # un numero molto piccolo (in modo da evitare le criticità del modello QDA di Scikit-Learn)
    for i,x in enumerate(tsret["Today"]):
        if (abs(x) < 0.0001):
            tsret["Today"][i] = 0.0001

    # Crea la colonna dei rendimenti percentuali ritardati
    for i in range(0, lags):
        tsret["Lag%s" % str(i+1)] = tslag["Lag%s" % str(i+1)].pct_change()*100.0

    # Crea la colonna "Direction" (+1 or -1) che indica un giorno rialzista/ribassista
    tsret["Direction"] = np.sign(tsret["Today"])
    tsret = tsret[tsret.index >= start_date]

    return tsret

if __name__ == "__main__":
    # Crea una serie ritardata dell'indice S&P500 del mercato azionario US
    snpret = create_lagged_series(
        "^GSPC", datetime.datetime(2001,1,10),
        datetime.datetime(2005,12,31), lags=5
       )

    # Uso il rendimento dei due giorni precedentei come valore
    # di predizione, con la direzione come risposta
    X = snpret[["Lag1","Lag2"]]
    y = snpret["Direction"]

    # I dati di test sono divisi in due parti: prima e dopo il 1 gennaio 2005.
    start_test = datetime.datetime(2005,1,1)

    # Crea il dataset di training e di test
    X_train = X[X.index < start_test]
    X_test = X[X.index >= start_test]
    y_train = y[y.index < start_test]
    y_test = y[y.index >= start_test]

    # Crea i modelli (parametrizzati)
    print("Hit Rates/Confusion Matrices:\n")
    models = [("LR", LogisticRegression()),
              ("LDA", LDA()),
              ("QDA", QDA()),
              ("LSVC", LinearSVC()),
              ("RSVM", SVC(
                 C=1000000.0, cache_size=200, class_weight=None,
                 coef0=0.0, degree=3, gamma=0.0001, kernel='rbf',
                 max_iter=-1, probability=False, random_state=None,
                 shrinking=True, tol=0.001, verbose=False)
                ),
              ("RF", RandomForestClassifier(
                 n_estimators=1000, criterion='gini',
                 max_depth=None, min_samples_split=2,
                 min_samples_leaf=1, max_features='auto',
                 bootstrap=True, oob_score=False, n_jobs=1,
                 random_state=None, verbose=0)
                )]

    # Iterazione attraverso i modelli
    for m in models:

        # Addestramento di ogni modello con il set di dati di training
        m[1].fit(X_train, y_train)

        # Costruisce un array di predizioni sui dati di test
        pred = m[1].predict(X_test)

        # Stampa del hit-rate e della confusion matrix di ogni modello.
        print("%s:\n%0.3f" % (m[0], m[1].score(X_test, y_test)))
        print("%s\n" % confusion_matrix(pred, y_test))