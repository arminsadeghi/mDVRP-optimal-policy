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
width = 8  # 3.487
height = width / 1.5


def parse_state_data(files):

    sb.set_theme(style="darkgrid")
    sb.set()

    colours = XKCD_ColourPicker()
    cols = []
    cols.extend(colours.values(1, "adobe"))
    cols.extend(colours.values(1, "darkish pink"))
    cols.extend(colours.values(1, "straw"))
    cols.extend(colours.values(1, "rich blue"))
    cols.extend(colours.values(1, "olive green"))

    colours_policy = colours.values(2)

    colours_lambda = [
        colours.values(6), colours.values(9),
    ]

    plt.rc('font', family='serif', serif='Times')
    plt.rc('text', usetex=True)
    plt.rc('xtick', labelsize=8)
    plt.rc('ytick', labelsize=8)
    plt.rc('axes', labelsize=8)

    df_list = []

    for f in files:
        df = pd.read_csv(f)
        try:
            df['cost-exponent'] = df['cost_exponent']
        except KeyError:
            pass
        df_list.append(df)

    df = pd.concat(df_list, ignore_index=True, sort=False)

    # for l, h, label in [(0, 0.5, 'low'), (0.5, 20, 'high')]:
    for l, h, label in [(0, 0.5, 'low'), (0.5, 20, 'high')]:
        for col in ['avg-wait-time', 'max-wait-time', 'total-travel-distance', 'avg-task-dist']:
            colour_index = 0
            fig, ax = plt.subplots()
            fig.subplots_adjust(left=.15, bottom=.16, right=.99, top=.97)

            # for df in df_list:
            df_slice = df[(df['lambda'] >= l) * (df['lambda'] <= h)]
            # df_slice = df_slice[(df_slice['cost-exponent'] >= -1) * (df_slice['cost-exponent'] <= 10)]
            n = len(set(df_slice['cost-exponent']))
            colour_list = colours.values(n)
            sb.lineplot(x='lambda', y=col, hue='cost-exponent', data=df_slice, palette=colour_list, linewidth=2.5)

            ax.set_xlabel("Lambda")
            # ax.set_ylabel("Speed (m/s)")
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles=handles[0:], labels=labels[0:], loc='upper left', title='Cost Exponent (p)')
            fig.set_size_inches(width, height)
            fig.savefig('plot_lamda_{}_{}.pdf'.format(col, label))

    for l, h, label in [(0, 0.5, 'low'), (0.5, 20, 'high')]:
        for col in ['avg-wait-time', 'max-wait-time', 'total-travel-distance', 'avg-task-dist']:
            colour_index = 0
            fig, ax = plt.subplots()
            fig.subplots_adjust(left=.15, bottom=.16, right=.99, top=.97)

            # sb.lineplot(x='lambda', y=col, hue='cost-exponent', data=df_slice, palette=colour_list, linewidth=2.5)

            df_slice = df[(df['lambda'] >= l) * (df['lambda'] <= h)]
            # df_slice = df_slice[(df_slice['cost-exponent'] >= -1) * (df_slice['cost-exponent'] <= 10)]
            n = len(set(df_slice['lambda']))
            colour_list = colours.values(n)
            sb.lineplot(x='cost-exponent', y=col, hue='lambda', data=df_slice, palette=colour_list, linewidth=2.5)

            ax.set_xlabel("Cost Exponent")
            # ax.set_ylabel("Speed (m/s)")
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles=handles[0:], labels=labels[0:], title='Lambda')
            fig.set_size_inches(width, height)
            fig.savefig('plot_cost_{}_{}.pdf'.format(col, label))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Vehicle State Parser")
    parser.add_argument(
        '-f', '--file', nargs='*', default=[],
        help='list of stat files to load')

    args = parser.parse_args()
    parse_state_data(args.file)
