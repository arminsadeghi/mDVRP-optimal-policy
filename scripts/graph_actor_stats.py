from enum import IntEnum
import re
import sys
import argparse
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sb
import numpy as np
from distinctipy import distinctipy


mpl.use('pdf')


# width as measured in inkscape
width = 8  # 3.487
height = width / 1.5


def parse_state_data(files):

    sb.set_theme(style="darkgrid")
    sb.set()

    plt.rc('font', family='serif', serif='Times')
    plt.rc('text', usetex=True)
    plt.rc('xtick', labelsize=8)
    plt.rc('ytick', labelsize=8)
    plt.rc('axes', labelsize=8)

    # read in and concatenate the data files
    df_list = []
    for f in files:
        df = pd.read_csv(f)
        df_list.append(df)
    df = pd.concat(df_list, ignore_index=True, sort=False)

    group = 'cost-exponent'
    n = len(set(df[group]))
    colour_list = distinctipy.get_colors(n)  # colours.values(n)

    fig, ax = plt.subplots()
    fig.subplots_adjust(left=.15, bottom=.16, right=.99, top=.97)

    col = 'changes'
    sb.lineplot(x='time', y=col, hue=group, data=df, palette=colour_list, linewidth=2.5)

    ax.set_ylabel("Change Counter")
    ax.set_xlabel("Time (s)")
    handles, labels = ax.get_legend_handles_labels()
    if len(args.labels):
        labels = args.labels
    ax.legend(handles=handles, labels=labels, title='Changes/Redirects vs Time')
    fig.set_size_inches(width, height)
    fig.savefig('plot_actor_{}.pdf'.format(col))

    fig, ax = plt.subplots()
    fig.subplots_adjust(left=.15, bottom=.16, right=.99, top=.97)

    col = 'path-len'
    sb.lineplot(x='time', y=col, hue=group, data=df, palette=colour_list, linewidth=2.5)

    ax.set_ylabel("Number of Outstanding Tasks")
    ax.set_xlabel("Time (s)")
    handles, labels = ax.get_legend_handles_labels()
    if len(args.labels):
        labels = args.labels
    ax.legend(handles=handles, labels=labels, title='Actor Path Length vs Time')
    fig.set_size_inches(width, height)
    fig.savefig('plot_actor_{}.pdf'.format(col))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Vehicle State Parser")
    parser.add_argument(
        '-f', '--file', nargs='*', default=[],
        help='list of stat files to load')
    parser.add_argument(
        '-l', '--labels', nargs='*', default=[],
        help='list of labels, one per data line/group')

    args = parser.parse_args()
    parse_state_data(args.file)
