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


def parse_state_data(files, names):

    sb.set_theme(style="darkgrid")
    sb.set()

    col = XKCD_ColourPicker()
    cols = col.values(30)

    plt.rc('font', family='serif', serif='Times')
    plt.rc('text', usetex=True)
    plt.rc('xtick', labelsize=8)
    plt.rc('ytick', labelsize=8)
    plt.rc('axes', labelsize=8)

    df_list = []

    for f in files:
        df = pd.read_csv(f)
        df_list.append(df)

    for col in ['avg-wait-time', 'max-wait-time', 'total-travel-distance', 'avg-task-dist', 'wait-sd']:
        colour_index = 0
        fig, ax = plt.subplots()
        fig.subplots_adjust(left=.15, bottom=.16, right=.99, top=.97)

        for df in df_list:
            colour_index += 1
            sb.lineplot(x='lambda', y=col, hue='policy', data=df, palette=[cols[colour_index]], linewidth=2.5)

        ax.set_xlabel("Lambda")
        # ax.set_ylabel("Speed (m/s)")
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles=handles[0:], labels=labels[0:])
        fig.set_size_inches(width, height)
        fig.savefig('plot_{}.pdf'.format(col))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Vehicle State Parser")
    parser.add_argument(
        '-f', '--file', nargs='*', default=[],
        help='CSV file(s) with car states in order:  X, Y, Z, Yaw, Vx, Vy, Ax, Ay')

    parser.add_argument(
        '-n', '--names', nargs='*', default=[],
        help='CSV file(s) with car states in order:  X, Y, Z, Yaw, Vx, Vy, Ax, Ay')

    args = parser.parse_args()
    parse_state_data(args.file, args.names)
