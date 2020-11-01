# https://datatrading.info/value-at-risk-var-per-il-risk-management-nel-trading-algoritmico/

# var.py

import datetime
import numpy as np
from pandas_datareader import data as pdr
from scipy.stats import norm


def var_cov_var(P, c, mu, sigma):
    """
    Calcolo della varianza-covarianza del Value-at-Risk giornaliero
    utilizzando il livello di confidenza c, con media dei rendimenti mu
    e la deviazione standard dei rendimenti sigma, su un portafoglio
    di valore P.
    """
    alpha = norm.ppf(1-c, mu, sigma)
    return P - P*(alpha + 1)

if __name__ == "__main__":
    ticker = "C"
    start = datetime.datetime(2010, 1, 1)
    end = datetime.datetime(2014, 1, 1)

    citi = pdr.get_data_yahoo(ticker, start, end)
    citi["rets"] = citi["Adj Close"].pct_change()

    P = 1e6   # 1,000,000 USD
    c = 0.99  # 99% intervallo di confidenza
    mu = np.mean(citi["rets"])
    sigma = np.std(citi["rets"])

    var = var_cov_var(P, c, mu, sigma)
    print("Value-at-Risk: {}0.2f".format(var))