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
from os import listdir
from os.path import isfile, join

# mpl.use('pdf')


# width as measured in inkscape
width = 8  # 3.487
height = width / 1.5


def reconstruct_policy_label(tags, meta_data, offset):
    # print(tags)
    if tags[offset-6] == 'trp':
        return '$c^p$-$\mathtt{BATCH}$, $\eta='+str(meta_data['eta']) + '$, $p='+str(meta_data['p'])+'$'
        # return 'LKH-Batch-TRP'
    elif tags[offset-6] == 'tsp':
        if tags[offset-7] == 'batch':
            if meta_data['p'] == -2:
                return '$\eta$-$\mathtt{BATCH}$, $\eta=1.0$'
            else:
                if meta_data['sectors'] > 1.0:
                    return 'DC-$\mathtt{BATCH}$, $\eta=' + str(meta_data['eta'])+'$, $r=' + str(meta_data['sectors'])+'$'
                else:
                    return '$\eta$-$\mathtt{BATCH}$, $\eta=' + str(meta_data['eta'])+'$'
        else:
            return '$\mathtt{Event}$, $p=1.5$'
    return 'None'


def plot_comparison(files, mode='baselines'):

    sb.set_theme(style="whitegrid")
    sb.set()

    plt.rc('font', family='serif', serif='Times')
    plt.rc('text', usetex=True)
    plt.rc('xtick', labelsize=16)
    plt.rc('ytick', labelsize=16)
    plt.rc('axes', labelsize=12)

    df_list = []
    for f in files:
        if 'DeliveryLog_' in f:
            df = pd.read_csv(f)
            try:
                df['cost-exponent'] = df['cost_exponent']
            except KeyError:
                pass
            if not 'sectors' in df.columns:
                df['sectors'] = 1

            tags = f.split('_')  # get meta data
            offset = 1 if '1.0t' in tags[-1] else 0

            if tags[offset-6][-2:] == 'sc':
                sectors = int(tags[offset-6][0:-2])
                tags.pop(offset-6)
            else:
                sectors = 1

            meta_data = {'lambda': float(tags[offset-3][0:-1]),                                              # tagged 'l'
                         'eta': float(tags[offset-4][0:-1]),                                                 # tagged 'e'
                         'p': float(tags[offset-5][0:-1]) if float(tags[offset-5][0:-1]) != -5 else 1.5,       # tagged 'p'
                         'sectors': sectors,                                                                 # tagged 'sc'
                         }

            meta_data['Solver'] = reconstruct_policy_label(tags, meta_data, offset)
            for key in meta_data.keys():
                df[key] = meta_data[key]
            df['Wait Time'] = df['t_service'] - df['t_arrive']
            df_list.append(df)

    df = pd.concat(df_list, ignore_index=True, sort=False)

    graphs = [(0.5, 0.9, 'high')]
    # graphs = [(0.7, 0.7, 'high')]

    if mode == 'baselines':
        colours = [
            'royalblue',  # 'slateblue',
            'lavender',
            'dodgerblue',  # 'lightsteelblue',
            'darkorange',
            # 'bisque',
            'linen'
        ]

        hue_order = [
            '$\eta$-$\mathtt{BATCH}$, $\eta=1.0$',
            # '$\eta - \mathtt{BATCH}$, $\eta=1.0$, $r=4$',
            #  '$\eta - \mathtt{BATCH}$, $\eta=0.5$',
            '$\eta$-$\mathtt{BATCH}$, $\eta=0.2$',
            'DC-$\mathtt{BATCH}$, $\eta=1.0$, $r=10$',
            '$c^p$-$\mathtt{BATCH}$, $\eta=0.2$, $p=1.5$',
            # '$c^p$-$\mathtt{BATCH}$, $\eta=0.2$, $p=2.0$',
            # '$c^p$-$\mathtt{BATCH}$, $\eta=0.2$, $p=3.0$',
            # '$c^p - \mathtt{BATCH}$, $(p=1.5)$ $\eta=0.5$',
            # '$\mathtt{Event}$, $p=1.5$'
        ]

    elif mode == 'differentP':
        hue_order = [
            '$c^p$-$\mathtt{BATCH}$, $\eta=0.2$, $p=1.0$',
            # '$c^p - \mathtt{BATCH}$, $\eta=0.2$, $p=1.1$',
            '$c^p$-$\mathtt{BATCH}$, $\eta=0.2$, $p=1.5$',
            '$c^p$-$\mathtt{BATCH}$, $\eta=0.2$, $p=2.0$',
            '$c^p$-$\mathtt{BATCH}$, $\eta=0.2$, $p=3.0$',
            # '$c^p - \mathtt{BATCH}$, $\eta=0.2$, $p=5.0$',
            '$c^p$-$\mathtt{BATCH}$, $\eta=0.2$, $p=10.0$',
        ]

        colours = [
            'lightblue',
            # 'slateblue',
            # 'lavender',
            'darkorange',
            'violet',
            # 'bisque',
            'aliceblue',
            'dodgerblue',
            'aquamarine',
        ]
    elif mode == 'Variance':
        hue_order = [
            '$c^p$-$\mathtt{BATCH}$, $\eta=0.2$, $p=1.5$',
            # '$c^p - \mathtt{BATCH}$, $\eta=0.2$, $p=5.0$',
            '$\eta$-$\mathtt{BATCH}$, $\eta=1.0$',
            # '$\eta - \mathtt{BATCH}$, $\eta=1.0$, $r=4$',
            #  '$\eta - \mathtt{BATCH}$, $\eta=0.5$',
            '$\eta$-$\mathtt{BATCH}$, $\eta=0.2$',
            'DC-$\mathtt{BATCH}$, $\eta=1.0$, $r=10$',
        ]

        colours = [
            'deepskyblue',
            # 'slateblue',
            # 'lavender',
            'darkorange',
            'lightsteelblue',
            # 'bisque',
            'cyan',
            'mediumpurple',
            'aquamarine',
        ]
    else:
        print('No PIC for you! Two weeks!!')
        return

    # df_trim = []
    # for hue in hue_order:
    #     df_hue = df.loc[df['Solver'] == hue]
    #     df_hue = df_hue.iloc[-100000:-1000, :]
    #     df_trim.append(df_hue)
    # df = pd.concat(df_trim, ignore_index=True, sort=False)

    df_var = pd.DataFrame(columns=['hue', 'lambda', 'mean', 'var'])

    if mode == 'Variance':
        lambs = [0.5, 0.6, 0.7, 0.8, 0.9]
        for hue in hue_order:
            for lamb in lambs:
                df_slice = df[(df['lambda'] == lamb)]
                df_slice = df_slice[(df_slice['Solver'] == hue)]
                df_var = pd.concat([pd.DataFrame([[hue, lamb, df_slice['Wait Time'].mean(), df_slice['Wait Time'].var()]],
                                                 columns=df_var.columns), df_var], ignore_index=True)

        print(df_var)

        fig, ax = plt.subplots()
        fig.subplots_adjust(left=.15, bottom=.16, right=.99, top=.97)
        sb.lineplot(x='lambda', y='mean', hue='hue', data=df_var, linewidth=2.5)

        # ax.set_yscale('log')
        ax.set_xlabel("$\\rho$", fontsize=20)
        ax.set_ylabel("Variance", fontsize=20)
        ax.tick_params(axis='both', which='major', labelsize=16)
        ax.legend(title='Method/Exponent', title_fontsize=18, fontsize=16)
        fig.set_size_inches(width, height)
        fig.savefig('VariancePlot.pdf')

        plt.show()
        return

    styles = ['Box']
    for style in styles:
        for l, h, label in graphs:
            sb.set_theme(style="whitegrid")
            fig, ax = plt.subplots()
            fig.subplots_adjust(left=.15, bottom=.16, right=.99, top=.97)

            # for df in df_list:
            df_slice = df[(df['lambda'] >= l) * (df['lambda'] <= h)]
            # sb.lineplot(x='lambda', y=col, hue='display-name', data=df_slice, palette=colours, linewidth=2.5)
            # if style == 'Violins':
            #     sb.violinplot(x='lambda', y='Wait Time', hue='Solver', hue_order=hue_order, data=df_slice, cut=0,
            #                   inner=None, palette=colours)
            #     ax.set_ylim([-10,300])
            if style == 'Box':
                flierprops = dict(marker='o', markerfacecolor='grey', markersize=2, alpha=.5,
                                  linestyle='none')
                sb.boxplot(x='lambda', y='Wait Time', hue='Solver', hue_order=hue_order, data=df_slice,  showfliers=True,
                           showmeans=True, palette=colours, flierprops=flierprops)
                ax.set_ylim([-10, 350])

            ax.set_xlabel("$\\rho$", fontsize=20)
            ax.set_ylabel("Wait Time (s)", fontsize=20)
            ax.tick_params(axis='both', which='major', labelsize=16)
            handles, labels = ax.get_legend_handles_labels()
            # ax.set_yscale('log')

            ax.legend(handles=handles, labels=labels, loc='upper left', title='Method/Exponent', title_fontsize=18, fontsize=16)
            fig.set_size_inches(width, height)
            fig.savefig(style+'_'+mode+'_plot_lamda_{}_{}.pdf'.format('WaitTime', label))
    plt.show()


if __name__ == "__main__":

    path = 'rcpy/'
    files = [path + '/' + f for f in listdir(path) if isfile(join(path, f))]
    plot_comparison(files, 'baselines')
    # plot_comparison(files, 'differentP')
    # plot_comparison(files, 'Variance')
