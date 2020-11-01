import datetime
import numpy as np
import pandas as pd
import quandl

def futures_rollover_weights(start_date, expiry_dates, contracts, rollover_days=5):
    """
    Si costruisce un DataFrame pandas che contiene pesi (tra 0,0 e 1,0)
    di posizioni contrattuali da mantenere per eseguire un rollover di rollover_days
    prima della scadenza del primo contratto. La matrice può quindi essere
    'moltiplicato' con un altro DataFrame contenente i prezzi di settle di ciascuno
    contratto al fine di produrre una serie temporali per un contratto future continuo.
    """

    # Costruisci una sequenza di date a partire dalla data inizio del primo contratto
    # alla data di fine del contratto finale
    dates = pd.date_range(start_date, expiry_dates[-1], freq='B')

    # Crea il DataFrame 'roll weights' che memorizzerà i moltiplicatori per
    # ogni contratto (tra 0,0 e 1,0)
    roll_weights = pd.DataFrame(np.zeros((len(dates), len(contracts))),
                                index=dates, columns=contracts)
    prev_date = roll_weights.index[0]

    # Si scorre ogni contratto e si crea i pesi specifiche per ogni
    # contratto che dipende dalla data di settlement e dai rollover_days
    for i, (item, ex_date) in enumerate(expiry_dates.iteritems()):
        if i < len(expiry_dates) - 1:
            roll_weights.ix[prev_date:ex_date - pd.offsets.BDay(), item] = 1
            roll_rng = pd.date_range(end=ex_date - pd.offsets.BDay(),
                                     periods=rollover_days + 1, freq='B')

            # Crea una sequenza di pesi rollover (cioè [0.0,0.2, ..., 0.8,1.0]
            # e si usano per regolare i pesi di ogni future
            decay_weights = np.linspace(0, 1, rollover_days + 1)
            roll_weights.ix[roll_rng, item] = 1 - decay_weights
            roll_weights.ix[roll_rng, expiry_dates.index[i+1]] = decay_weights
        else:
            roll_weights.ix[prev_date:, item] = 1
        prev_date = ex_date
    return roll_weights

if __name__ == "__main__":
    # Scarica gli attuali contratti future Front e Back (vicino e lontano)
    # per il petrolio WTI, negoziato al NYMEX, da Quandl.com. Avrai bisogno di
    # aggiustare i contratti per riflettere gli attuali contratti vicini / lontani
    # a seconda del punto in cui leggi questo!
    wti_near = quandl.get("OFDP/FUTURE_CLF2014")
    wti_far = quandl.get("OFDP/FUTURE_CLG2014")
    wti = pd.DataFrame({'CLF2014': wti_near['Settle'],
                        'CLG2014': wti_far['Settle']}, index=wti_far.index)

    # Crea un dizionario delle date di scadenza di ogni contratto
    expiry_dates = pd.Series({'CLF2014': datetime.datetime(2013, 12, 19),
                              'CLG2014': datetime.datetime(2014, 2, 21)}).order()

    # Calcolare la matrice (Dataframe) dei pesi di rollover
    weights = futures_rollover_weights(wti_near.index[0], expiry_dates, wti.columns)

    # Costruzione del future continuo dei contratti del petrolio WTI (CL)
    wti_cts = (wti * weights).sum(1).dropna()

    # Stammpa delle serie aggregate dei prezzi di settle dei contratti
    wti_cts.tail(60)