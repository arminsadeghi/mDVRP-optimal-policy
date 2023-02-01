#
# A short script to parse the data from the Montreal 2017-2019 311 data set and extract the service requests that
# include the lat/log as  location data
#
# Data set can be found at: https://open.canada.ca/data/en/dataset/5866f832-676d-4b07-be6a-e99c21eb17e4
#

import pandas as pd
import argparse
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sb
import distinctipy

from sklearn.cluster import KMeans

# No google for you -- licences are too restrictive re: data usage
# import googlemaps
import requests
import json

# Sample entry:
#  "19-99823", "Requete", "Dépôt illégal - Déchets","Adresse", "avenue 9e",
#  "", "", "0.0", "Villeray-Saint-Michel - Parc-Extension", "Villeray-Saint-Michel-Parc-Extension", "",
#  "2019-03-20T15:28:30","Courriel",
#  "0","1","0","0","0","0","0","0","0",
#  "VILLERAY - ST-MICHEL - PARC-EXTENSION",
#  "-73.62228842901318", "45.56816000746736",
#  "295254.6669081344", "5047590.628765508",
#  "Terminée","2019-04-18T14:56:25"

ORIGINAL_COLUMNS = [
    "ID_UNIQUE",
    "NATURE",            # Requete
    "ACTI_NOM",
    "TYPE_LIEU_INTERV",  # Address / Intersection
    "RUE",               # if an address
    "RUE_INTERSECTION1",  # if an intersection
    "RUE_INTERSECTION2",  # if an intersection
    "ARRONDISSEMENT",
    "ARRONDISSEMENT_GEO",
    "LIN_CODE_POSTAL",
    "DDS_DATE_CREATION",
    "PROVENANCE_ORIGINALE",
    "PROVENANCE_TELEPHONE",
    "PROVENANCE_COURRIEL",
    "PROVENANCE_PERSONNE",
    "PROVENANCE_COURRIER",
    "PROVENANCE_TELECOPIEUR",
    "PROVENANCE_INSTANCE",
    "PROVENANCE_MOBILE",
    "PROVENANCE_MEDIASOCIAUX",
    "PROVENANCE_SITEINTERNET",
    "UNITE_RESP_PARENT",
    "LOC_LONG",
    "LOC_LAT",
    "LOC_X",
    "LOC_Y",
    "DERNIER_STATUT",
    "DATE_DERNIER_STATUT"
]


# reduce the columns to just those for processing requests (id, type, location, creation, lat/long)
FILTERED_COLUMNS = [
    "ID_UNIQUE",
    "NATURE",            # Requete
    "ACTI_NOM",
    "TYPE_LIEU_INTERV",  # Address / Intersection
    "RUE",               # if an address
    "RUE_INTERSECTION1",  # if an intersection
    "RUE_INTERSECTION2",  # if an intersection
    "ARRONDISSEMENT",
    "ARRONDISSEMENT_GEO",
    "LIN_CODE_POSTAL",
    "DDS_DATE_CREATION",
    "UNITE_RESP_PARENT",
    "LOC_LONG",
    "LOC_LAT",
]

DISTANCE_COLUMNS = [
    "SEED",
    "SRC_ID_UNIQUE",
    "SRC_LOC_LONG",
    "SRC_LOC_LAT",
    "DST_ID_UNIQUE",
    "DST_LOC_LONG",
    "DST_LOC_LAT",
    "DISTANCE",
    "TRAVEL_TIME"
]

CLUSTERED_COLUMNS = [
    "SEED",
    "ID_UNIQUE",
    "LOC_LONG",
    "LOC_LAT",
    "X",
    "Y",
    "DEPOT",
    "CLUSTER",
]


NATURE_OF_SERVICE = 'Requete'
BOROUGH_OF_SERVICE = 'Montréal-Nord'


def load_data(args):
    df = pd.read_csv(args.input)
    rng = np.random.default_rng(seed=args.seed)
    rows = rng.integers(len(df), size=[args.samples,])
    return df.iloc[rows]


def visualize(df):
    fig, ax = plt.subplots()
    fig.subplots_adjust(left=.15, bottom=.16, right=.99, top=.97)
    colours = distinctipy.get_colors(n_colors=args.clusters, colorblind_type='Deuteranomaly')

    sb.scatterplot(data=df, x='X', y='Y', hue='CLUSTER', palette=colours, style='DEPOT', markers=['o', 's'], sizes=[25, 65], size='DEPOT')
    plt.show(block=True)


def cluster_data(args, df):

    clustered_pts = []
    df = pd.DataFrame(df)

    min_lat = df['LOC_LAT'].min()
    max_lat = df['LOC_LAT'].max()
    min_long = df['LOC_LONG'].min()
    max_long = df['LOC_LONG'].max()

    # find the range for the data, scaled slightly to make the map look nice
    data_range = max(max_long - min_long, max_lat - min_lat) * 1.1
    lat_base = min_lat - (data_range - (max_lat - min_lat))/2
    long_base = min_long - (data_range - (max_long - min_long))/2
    df['X'] = (df['LOC_LONG'] - long_base) / data_range
    df['Y'] = (df['LOC_LAT'] - lat_base) / data_range

    clusters = KMeans(n_clusters=args.clusters, init='k-means++', n_init='auto').fit(df[['LOC_LAT', 'LOC_LONG']].to_numpy())

    df['CLUSTER'] = clusters.labels_
    df['SEED'] = args.seed
    df['DEPOT'] = False

    depots = []
    for i, centre in enumerate(clusters.cluster_centers_):
        entry = {
            "SEED": args.seed,
            "ID_UNIQUE": 'depot'+f'{i:002}',
            "LOC_LONG": centre[1],
            "LOC_LAT": centre[0],
            "X": (centre[1] - long_base) / data_range,
            "Y": (centre[0] - lat_base) / data_range,
            "CLUSTER": i,
            "DEPOT": True
        }
        depots.append(entry)

    return pd.concat((pd.DataFrame(depots), df))


def main(args):

    df = load_data(args)

    data = cluster_data(args, df)
    visualize(data)

    output = ".".join(args.input.split('.')[:-1] + ['clustered', 'csv'])
    data.to_csv(output, index=False)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description=__doc__)

    argparser.add_argument(
        '--input',
        default=None,
        type=str,
        help='Source CSV file')
    argparser.add_argument(
        '--seed',
        default=42,
        type=int,
        help='Random seed for generation')
    argparser.add_argument(
        '--clusters',
        default=2,
        type=int,
        help='Number of Clusters to create')
    argparser.add_argument(
        '--samples',
        default=2500,
        type=int,
        help='Number of samples to draw')

    args = argparser.parse_args()

    main(args)
