import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

def get_unique(df: pd.DataFrame):
    df_sorted = df.sort_values('fecha').reset_index(drop=True)

    x = []
    y = []

    for i in range(len(df)):
        uniques = len(df_sorted[['artista', 'cancion']][:i].drop_duplicates())
        x.append(i)
        y.append(uniques)

    return x, y

def get_model(x, y):
    x = np.array(x)
    y = np.array(y)

    def model(x, n):
        return n * (1 - np.exp(-x / n))

    # ajuste
    popt, _ = curve_fit(model, x, y, p0=[2000])
    n_hat = popt[0]

    return model, n_hat

def plot_curve(df: pd.DataFrame):
    x, y = get_unique(df)
    model, n_hat = get_model(x, y)

    x_future = np.arange(x[-1]+1, x[-1]*5)
    y_future = model(x_future, n_hat)

    plt.plot(x, y, label='Actual')
    plt.plot(x_future, y_future, label='Futuro')
    plt.xlabel("Total")
    plt.ylabel("No repetidas")
    plt.legend()
    plt.title(f"Curva n={int(n_hat)}")
    plt.show()