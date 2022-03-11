from xkcdColour import XKCD_ColourPicker
from enum import IntEnum
import re
import sys
import argparse
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sb
import numpy as np

mpl.use('pdf')


# width as measured in inkscape
width = 3.487
height = width / 1.5


def parse_state_data(files):

    sb.set_theme(style="darkgrid")
    sb.set()

    col = XKCD_ColourPicker()
    cols = []
    cols.extend(col.values(1, "adobe"))
    cols.extend(col.values(1, "darkish pink"))
    cols.extend(col.values(1, "straw"))
    cols.extend(col.values(1, "rich blue"))
    cols.extend(col.values(1, "olive green"))

    plt.rc('font', family='serif', serif='Times')
    plt.rc('text', usetex=True)
    plt.rc('xtick', labelsize=8)
    plt.rc('ytick', labelsize=8)
    plt.rc('axes', labelsize=8)

    df_list = []

    for f in files:
        df = pd.read_csv(f)
        df_list.append(df)

    for l, h, label in [(0, 0.5, 'low'), (0.5, 1.1, 'high')]:
        for col in ['avg-wait-time', 'max-wait-time', 'total-travel-distance', 'avg-task-dist', 'wait-sd', 'sim-time']:
            colour_index = 0
            fig, ax = plt.subplots()
            fig.subplots_adjust(left=.15, bottom=.16, right=.99, top=.97)

            for df in df_list:
                colour_index += 1
                df_slice = df[(df['lambda'] >= l) * (df['lambda'] <= h)]
                sb.lineplot(x='lambda', y=col, hue='policy', data=df_slice, palette=[cols[colour_index]], linewidth=2.5)

            ax.set_xlabel("Lambda")
            # ax.set_ylabel("Speed (m/s)")
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles=handles[0:], labels=labels[0:])
            fig.set_size_inches(width, height)
            fig.savefig('plot_{}_{}.pdf'.format(col, label))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Vehicle State Parser")
    parser.add_argument(
        '-f', '--file', nargs='*', default=[],
        help='list of stat files to load')

    args = parser.parse_args()
    parse_state_data(args.file)
