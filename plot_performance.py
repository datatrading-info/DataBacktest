# plot_performance.py

import os.path
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

if __name__ == "__main__":
    data = pd.io.parsers.read_csv(
        "equity.csv", header=0,
        parse_dates=True, index_col=0
    )

    # Visualizza tre grafici: curva di Equity,
    # rendimenti, drawdown
    fig = plt.figure()

    # Imposta il bianco come colore di sfondo
    fig.patch.set_facecolor('white')

    # Visualizza la curva di equity
    ax1 = fig.add_subplot(311, ylabel='Portfolio value, % ')
    data['equity_curve'].plot(ax=ax1, color="blue", lw=2.)
    plt.grid(True)

    # Visualizza i rendimenti
    ax2 = fig.add_subplot(312, ylabel='Period returns, % ')
    data['returns'].plot(ax=ax2, color="black", lw=2.)
    plt.grid(True)

    # Visualizza i drawdown
    ax3 = fig.add_subplot(313, ylabel='Drawdowns, % ')
    data['drawdown'].plot(ax=ax3, color="red", lw=2.)
    plt.grid(True)

    # Stampa i grafici
    plt.show()
    print("")