import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def plot_df_grid(df, date_col='Date', layout=None, figsize=(12, 10), sharex=True, grid=True):
    if date_col in df.columns:
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col)

    df_num = df.select_dtypes(include=[np.number])

    ncols = int(np.ceil(np.sqrt(len(df_num.columns)))) if layout is None else layout[1]
    nrows = int(np.ceil(len(df_num.columns) / ncols)) if layout is None else layout[0]
    layout = (nrows, ncols)

    axes = df_num.plot(
        subplots=True,
        layout=layout,
        figsize=figsize,
        legend=False,
        grid=grid,
        sharex=sharex
    )

    for ax, col in zip(axes.flat, df_num.columns):
        ax.set_title(col, fontsize=10)
        ax.set_ylabel("")

    for ax in axes.flat[len(df_num.columns):]:
        ax.set_visible(False)

    plt.tight_layout()
    plt.show()