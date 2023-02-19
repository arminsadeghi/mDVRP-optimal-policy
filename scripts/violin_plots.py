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

mpl.use('pdf')
# import scienceplots
# plt.style.use(['science', 'ieee'])

# width as measured in inkscape
width = 8  # 3.487
height = width / 1.5


def export_table2(df, hues):

    print('%%%%%')
    print('% Table Data for Uniform Distribution in metric space')
    print('%')
    print('\\begin{table*}')
    print('\\caption{Mean, Median and Average Task Wait Times (m)}')
    print('\\label{table:task-time-data}')
    print('\\begin{center}')
    print('\\begin{tabular}{@{} l c c c | c c c | c c c | c c c | c c c @{}}')
    print('\\toprule')
    print(' & \\multicolumn{3}{c}{$\\rho=0.5$} & \\multicolumn{3}{c}{$\\rho=0.6$} & \\multicolumn{3}{c}{$\\rho=0.7$} & \\multicolumn{3}{c}{$\\rho=0.8$} & \\multicolumn{3}{c}{$\\rho=0.9$} \\\\')
    print('Method & Mean  & $\\sigma$ & 95\% & Mean  & $\\sigma$ & 95\% & Mean  & $\\sigma$ & 95\% & Mean  & $\\sigma$ & 95\% & Mean & $\\sigma$ & 95\% \\\\')
    print('\\midrule')

    for hue in hues:
        s = hue
        for rho in [0.5, 0.6, 0.7, 0.8, 0.9]:
            df_slice = df[(df['Solver'] == hue) & (df['rho'] == rho)]
            # s += ' & ' + f"{(df_slice['Wait Time'].mean()):5.2f} & {(df_slice['Wait Time'].std()):5.2f} & {(df_slice['Wait Time'].quantile(q=0.95)):5.2f}"
            s += ' & ' + f"{(df_slice['wait_minutes'].mean()):5.2f} & {(df_slice['wait_minutes'].std()):5.2f} & {(df_slice['wait_minutes'].quantile(q=0.95)):5.2f}"
        s += "\\\\"
        print(s)

    print('\\bottomrule')
    print('\\end{tabular}')
    print('\\end{center}')
    print('\\end{table*}')
    print('%')
    print('%%%%%')


def export_table(df, hues):

    print('%%%%%')
    print('% Table Data for Uniform Distribution in metric space')
    print('%')
    print('\\begin{table}')
    print('\\caption{Mean, Median and Average Task Wait Times (s)}')
    print('\\label{table:task-time-data}')
    print('\\begin{center}')
    print('\\begin{tabular}{@{} l l c c c c @{}}')
    print('\\toprule')
    print('$\\rho$ & Method & Mean & Median & $\\sigma$ & 95\% \\\\')

    for rho in [0.5, 0.6, 0.7, 0.8, 0.9]:
        print('\\midrule')
        rho_str = str(rho)
        for hue in hues:
            df_slice = df[(df['Solver'] == hue) & (df['rho'] == rho)]
            # print(
            #     f"{rho_str} & {hue} & {(df_slice['Wait Time'].mean()):5.2f} & {(df_slice['Wait Time'].median()):5.2f} & {(df_slice['Wait Time'].std()):5.2f} & {(df_slice['Wait Time'].quantile(q=0.95)):5.2f} \\\\")
            print(
                f"{rho_str} & {hue} & {(df_slice['wait_minutes'].mean()):5.2f} & {(df_slice['wait_minutes'].median()):5.2f} & {(df_slice['wait_minutes'].std()):5.2f} & {(df_slice['wait_minutes'].quantile(q=0.95)):5.2f} \\\\")
            rho_str = ''

    print('\\bottomrule')
    print('\\end{tabular}')
    print('\\end{center}')
    print('\\end{table}')
    print('%')
    print('%%%%%')


def reconstruct_policy_label(tags, meta_data, offset):
    # print(tags)
    if tags[offset-6] == 'time':
        tags.pop(offset-6)

    if tags[offset-6] == 'trp':
        if tags[offset-7] == 'cont':
            return '$c^p$-$\mathtt{CONT}$ $p$=$'+str(meta_data['p'])+'$'
        else:
            if meta_data['eta'] == 0.05:
                return '$\mathtt{PROPOSED}$'
            else:
                return '$c^p$-$\mathtt{BATCH}$ $\eta$=$'+str(meta_data['eta']) + '$ $p$=$'+str(meta_data['p'])+'$'
        # return 'LKH-Batch-TRP'
    elif tags[offset-6] == 'tsp':
        if tags[offset-7] == 'batch':
            if meta_data['p'] == -2:
                return '$\eta$-$\mathtt{BATCH}$ $\eta$=$1.0$'
            else:
                if meta_data['sectors'] > 1.0:
                    return '$\mathtt{DC}$-$\mathtt{BATCH}$'  # , $\eta=' + str(meta_data['eta']) + '$, $r=' + str(meta_data['sectors'])+'$'
                else:
                    return '$\eta$-$\mathtt{BATCH}$ $\eta$=$' + str(meta_data['eta']) + '$'
        else:
            return '$\mathtt{Event}$ $p$=$1.5$'
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
        if 'DeliveryLog_montreal_ral' in f:
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

            eta = tags[offset-4]
            eta = float(eta.strip('ef'))

            meta_data = {'lambda': float(tags[offset-3][0:-1]),                                              # tagged 'l'
                         'eta': eta,
                         'p': float(tags[offset-5][0:-1]) if float(tags[offset-5][0:-1]) != -5 else 1.5,       # tagged 'p'
                         'sectors': sectors,                                                                 # tagged 'sc'
                         }

            meta_data['Solver'] = reconstruct_policy_label(tags, meta_data, offset)
            for key in meta_data.keys():
                df[key] = meta_data[key]
            df['Wait Time'] = df['t_service'] - df['t_arrive']

            # TODO: Hardcoding the base delivery time if
            service_time = tags[offset-2][:-1]
            # df['rho'] = np.round((291 + float(service_time)) * meta_data['lambda'], 2)
            df['rho'] = np.round((float(service_time)) * meta_data['lambda'], 2)
            df['wait_minutes'] = np.round(df['Wait Time']/60.0, 2)
            df_list.append(df)

    df = pd.concat(df_list, ignore_index=True, sort=False)

    graphs = [(0.5, 1.0, 'high')]
    # graphs = [(0.7, 0.7, 'high')]

    if mode == 'baselines':
        colours = [
            'darkorange',
            'wheat',
            'royalblue',
            'lavender',
            'slateblue',


            'dodgerblue',
            'lightsteelblue',
            # 'bisque',
            'linen'
        ]

        hue_order = [
            '$\mathtt{PROPOSED}$',
            # '$c^p$-$\mathtt{BATCH}$, $\eta=0.05$, $p=1.5$',
            '$c^p$-$\mathtt{BATCH}$ $\eta$=$0.2$ $p$=$1.5$',
            '$\eta$-$\mathtt{BATCH}$ $\eta$=$1.0$',
            # '$\eta - \mathtt{BATCH}$, $\eta=1.0$, $r=4$',
            #  '$\eta - \mathtt{BATCH}$, $\eta=0.5$',
            '$\eta$-$\mathtt{BATCH}$ $\eta$=$0.2$',
            # '$\mathtt{DC}$-$\mathtt{BATCH}$, $\eta=1.0$, $r=10$',
            # '$\mathtt{DC}$-$\mathtt{BATCH}$',
            # '$c^p$-$\mathtt{BATCH}$, $\eta=1.0$, $p=1.5$',
            # '$c^p$-$\mathtt{BATCH}$, $\eta=0.2$, $p=2.0$',
            # '$c^p$-$\mathtt{BATCH}$, $\eta=1.0$, $p=2.0$',
            # '$c^p$-$\mathtt{CONT}$ $p$=$2.0$',
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
            # 'DC-$\mathtt{BATCH}$, $\eta=1.0$, $r=10$',
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

    df_var = pd.DataFrame(columns=['hue', 'rho', 'mean', 'var'])

    if mode == 'Variance':
        rhos = [0.5, 0.6, 0.7, 0.8, 0.9]
        for hue in hue_order:
            for rho in rhos:
                df_slice = df[(df['rho'] == rho)]
                df_slice = df_slice[(df_slice['Solver'] == hue)]
                df_var = pd.concat([pd.DataFrame([[hue, rho, df_slice['Wait Time'].mean(), df_slice['Wait Time'].var()]],
                                                 columns=df_var.columns), df_var], ignore_index=True)

        print(df_var)

        fig, ax = plt.subplots()
        fig.subplots_adjust(left=.15, bottom=.16, right=.99, top=.97)
        sb.lineplot(x='rho', y='mean', hue='hue', data=df_var, linewidth=2.5)

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
            sb.set_style(style="whitegrid")
            fig, ax = plt.subplots()
            fig.subplots_adjust(left=.15, bottom=.16, right=.99, top=.97)

            # for df in df_list:
            df_slice = df[(df['rho'] >= l) * (df['rho'] <= h)]
            # sb.lineplot(x='lambda', y=col, hue='display-name', data=df_slice, palette=colours, linewidth=2.5)
            # if style == 'Violins':
            #     sb.violinplot(x='lambda', y='Wait Time', hue='Solver', hue_order=hue_order, data=df_slice, cut=0,
            #                   inner=None, palette=colours)
            #     ax.set_ylim([-10,300])
            if style == 'Box':
                flierprops = dict(marker='o', markerfacecolor='grey', markersize=2, alpha=.5,
                                  linestyle='none')
                # sb.boxplot(x='rho', y='Wait Time', hue='Solver', hue_order=hue_order, data=df_slice,  showfliers=True,
                #            showmeans=True, palette=colours, flierprops=flierprops)
                sb.boxplot(x='rho', y='wait_minutes', hue='Solver', hue_order=hue_order, data=df_slice,  showfliers=True,
                           showmeans=True, palette=colours, flierprops=flierprops)
                ax.set_ylim([-1, 2500])

            ax.set_xlabel("$\\rho$", fontsize=20)
            ax.set_ylabel("Wait Time (m)", fontsize=20)
            ax.tick_params(axis='both', which='major', labelsize=16)
            handles, labels = ax.get_legend_handles_labels()
            # ax.set_yscale('log')

            ax.legend(handles=handles, labels=labels, loc='upper left', title='Method/Exponent', title_fontsize=18, fontsize=16)
            fig.set_size_inches(width, height)
            fig.savefig(style+'_'+mode+'_plot_lamda_{}_{}.pdf'.format('WaitTime', label))

    export_table(df, hues=hue_order)
    export_table2(df, hues=hue_order)


if __name__ == "__main__":

    path = 'results/'
    files = [path + '/' + f for f in listdir(path) if isfile(join(path, f))]
    plot_comparison(files, 'baselines')
    # plot_comparison(files, 'differentP')
    # plot_comparison(files, 'Variance')
