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
from distinctipy import distinctipy


mpl.use('pdf')


# width as measured in inkscape
width = 8  # 3.487
height = width / 1.5


def parse_state_data(files, prefix, eta, p):

    sb.set_theme(style="darkgrid")
    sb.set()

    if prefix is not None:
        prefix = prefix+'_'
    else:
        prefix = ''

    plt.rc('font', family='serif', serif='Times')
    plt.rc('text', usetex=True)
    plt.rc('xtick', labelsize=12)
    plt.rc('ytick', labelsize=12)
    plt.rc('axes', labelsize=12)

    df_list = []

    for f in files:
        df = pd.read_csv(f)
        try:
            df['cost-exponent'] = df['cost_exponent']
        except KeyError:
            pass
        df_list.append(df)

    df = pd.concat(df_list, ignore_index=True, sort=False)

    # extract some different relationships from the data frame
    df['avg-and-max-wait'] = df['avg-wait-time'] + df['max-wait-time']

    # df = df.loc[(df['cost-exponent'] >= -2) * (df['cost-exponent'] <= 2)]
    # df = df.loc[(df['lambda'] <= 0.95)]
    df = df.loc[
        # (df['cost-exponent'] == -4) +
        # (df['cost-exponent'] == -3) +
        (df['cost-exponent'] == -2) +
        (df['cost-exponent'] == -1) +
        (df['cost-exponent'] == 1) +
        (df['cost-exponent'] == 1.5) +
        (df['cost-exponent'] == 2)
    ]

    ces = set(df['cost-exponent'])
    etas = set(df['eta'])
    policies = set(df['policy'])
    
    for eta in etas:
        df_eta = df.loc[df['eta'] == eta]
        df_d = df_eta.loc[(df['cost-exponent'] == -2.0)]
        df_n = df_eta.loc[(df['cost-exponent'] == p)]
        df_eta.loc[(df_eta['cost-exponent'] == p), 'avg-ratio'] = df_n['avg-wait-time'].to_numpy() / df_d['avg-wait-time'].to_numpy()
        df_eta.loc[(df_eta['cost-exponent'] == p), 'max-ratio'] = df_n['max-wait-time'].to_numpy() / df_d['max-wait-time'].to_numpy()
        # df.loc[df['cost-exponent'] == ce, 'dist-ratio'] = df_n['total-travel-distance'].to_numpy() / df_d['total-travel-distance'].to_numpy()

        disp_postfix = " $\eta$ = "+str(eta)

        df_eta.loc[df_eta['cost-exponent'] == eta, 'display-name'] = disp_postfix

    # set the graph separations
    # graphs = [(0, 0.5, 'low'), (0.5, 1.0, 'high')]
    graphs = [(0.5, 0.8, 'high')]

    # plot vs cost exponent
    # df = df[(df['cost-exponent'] >= 1) * (df['cost-exponent'] <= 3)]
    n = len(set(df['display-name']))
    colour_list = distinctipy.get_colors(n)  # colours.values(n)
    # colour_list = ['#fa8888', '#ca1111', '#df6699', '#5555fa', '#0000ff', '#6662aa', '#11fc11', '#ffaa21']

    for l, h, label in graphs:
        # , 'avg-and-max-wait', 'avg-ratio', 'max-ratio', 'dist-ratio']:
        for col in ['avg-wait-time', 'max-wait-time']:
            colour_index = 0
            fig, ax = plt.subplots()
            fig.subplots_adjust(left=.15, bottom=.16, right=.99, top=.97)

            # for df in df_list:
            df_slice = df[(df['lambda'] >= l) * (df['lambda'] <= h)]
            sb.lineplot(x='lambda', y=col, hue='display-name', data=df_slice, palette=colour_list, linewidth=2.5)

            ax.set_xlabel("$\lambda$")
            ax.set_ylabel("Time (s)")
            handles, labels = ax.get_legend_handles_labels()
            # for i in range(len(labels)):
            #     if labels[i] == '-1.0':
            #         labels[i] = 'tsp'
            #     if labels[i] == '-2.0':
            #         labels[i] = 'batch'
            #     if labels[i] == '-3.0':
            #         labels[i] = '80/20 W'
            #     if labels[i] == '-4.0':
            #         labels[i] = '50/50 W'

            ax.legend(handles=handles, labels=labels, loc='upper left', title='Method/Exponent')
            fig.set_size_inches(width, height)
            fig.savefig('{}plot_lamda_{}_{}.pdf'.format(prefix, col, label))

        # for col in ['total-travel-distance', 'avg-task-dist']:
        #     colour_index = 0
        #     fig, ax = plt.subplots()
        #     fig.subplots_adjust(left=.15, bottom=.16, right=.99, top=.97)

        #     # for df in df_list:
        #     df_slice = df[(df['lambda'] >= l) * (df['lambda'] <= h)]
        #     sb.lineplot(x='lambda', y=col, hue='display-name', data=df_slice, palette=colours, linewidth=2.5)

        #     ax.set_xlabel("$\lambda$")
        #     ax.set_ylabel("Distance (m)")
        #     handles, labels = ax.get_legend_handles_labels()
        #     # for i in range(len(labels)):
        #     #     if labels[i] == '-1.0':
        #     #         labels[i] = 'tsp'
        #     #     if labels[i] == '-2.0':
        #     #         labels[i] = 'batch'
        #     #     if labels[i] == '-3.0':
        #     #         labels[i] = '80/20 W'
        #     #     if labels[i] == '-4.0':
        #     #         labels[i] = '50/50 W'

        #     ax.legend(handles=handles, labels=labels, loc='upper left', title='Method/Exponent')
        #     fig.set_size_inches(width, height)
        #     fig.savefig('{}plot_lamda_{}_{}.pdf'.format(prefix, col, label))

    # # plot vs Lambda
    # for l, h, label in graphs:
    #     n = len(set(df[(df['lambda'] >= l) * (df['lambda'] <= h)]['lambda']))
    #     colour_list = distinctipy.get_colors(n)  # colours.values(n)
    #     for col in ['avg-wait-time', 'max-wait-time', 'total-travel-distance', 'avg-task-dist', 'avg-and-max-wait', 'avg-ratio', 'max-ratio']:
    #         colour_index = 0
    #         fig, ax = plt.subplots()
    #         fig.subplots_adjust(left=.15, bottom=.16, right=.99, top=.97)

    #         df_slice = df[(df['lambda'] >= l) * (df['lambda'] <= h)]
    #         sb.lineplot(x='cost-exponent', y=col, hue='lambda', data=df_slice, palette=colour_list, linewidth=2.5)

    #         ax.set_xlabel("Cost Exponent")
    #         # ax.set_ylabel("Speed (m/s)")
    #         handles, labels = ax.get_legend_handles_labels()
    #         ax.legend(handles=handles[0:], labels=labels[0:], title='Lambda')
    #         fig.set_size_inches(width, height)
    #         fig.savefig('{}plot_cost_{}_{}.pdf'.format(prefix, col, label))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Vehicle State Parser")
    parser.add_argument(
        '-f', '--file', nargs='*', default=[],
        help='list of stat files to load')
    parser.add_argument(
        '-p', '--prefix', default=None,
        help='prefix to add to graph names')
    parser.add_argument(
        '--eta',
        default=1.0,
        type=float,
        help='Proportion of policy to execute (batch) (0,1]')
    parser.add_argument(
        '-c', '--cost-exponent',
        default=None,
        type=float,
        help='Power of Cost Function for Min Wait')

    args = parser.parse_args()
    parse_state_data(args.file, args.prefix, args.eta, args.cost_exponent)
