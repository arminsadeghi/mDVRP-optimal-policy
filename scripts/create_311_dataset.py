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

FILTERED_DATATYPES = {
    "ID_UNIQUE": str,
    "NATURE": str,            # Requete
    "ACTI_NOM": str,
    "TYPE_LIEU_INTERV": str,  # Address / Intersection
    "RUE": str,               # if an address
    "RUE_INTERSECTION1": str,  # if an intersection
    "RUE_INTERSECTION2": str,  # if an intersection
    "ARRONDISSEMENT": str,
    "ARRONDISSEMENT_GEO": str,
    "LIN_CODE_POSTAL": str,
    "DDS_DATE_CREATION": str,
    "UNITE_RESP_PARENT": str,
    "LOC_LONG": np.float64,
    "LOC_LAT": np.float64,
}

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

NATURE_OF_SERVICE = 'Requete'
BOROUGH_OF_SERVICE = 'Montréal-Nord'


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


def load_data(args):
    df = pd.read_csv(args.input, dtype=FILTERED_DATATYPES)
    rng = np.random.default_rng(seed=args.seed)
    rows = rng.integers(len(df), size=[args.samples,])
    return df.iloc[rows]


def visualize(df):
    fig, ax = plt.subplots()
    fig.subplots_adjust(left=.15, bottom=.16, right=.99, top=.97)
    sb.scatterplot(data=df, x='LOC_LONG', y='LOC_LAT')


def visualize_clusters(df):
    fig, ax = plt.subplots()
    fig.subplots_adjust(left=.15, bottom=.16, right=.99, top=.97)
    colours = distinctipy.get_colors(n_colors=args.clusters, colorblind_type='Deuteranomaly')
    sb.scatterplot(data=df, x='X', y='Y', hue='CLUSTER', palette=colours, style='DEPOT', markers=['o', 's'], sizes=[25, 65], size='DEPOT')


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
            "ID_UNIQUE": 'depot'+f'{i:03}',
            "LOC_LONG": centre[1],
            "LOC_LAT": centre[0],
            "X": (centre[1] - long_base) / data_range,
            "Y": (centre[0] - lat_base) / data_range,
            "CLUSTER": i,
            "DEPOT": True
        }
        depots.append(entry)

    return pd.concat((pd.DataFrame(depots), df)), long_base, lat_base, data_range


def collect_distance_data(args, df, long_base=0, lat_base=0, data_range=1):

    distances = []

    df = df.reset_index()
    clusters = df.CLUSTER.unique()

    for cluster in clusters:
        idx = df.index[df.CLUSTER == cluster]

        for si, src_row in df.loc[idx].iterrows():
            for di, dst_row in df.loc[idx].iterrows():

                if si == di:
                    continue

                response = requests.get(
                    f'http://localhost:5000/table/v1/driving/{src_row["LOC_LONG"]},{src_row["LOC_LAT"]};{dst_row["LOC_LONG"]},{dst_row["LOC_LAT"]}'
                )
                data1 = json.loads(response.text)
                if data1['code'] != 'Ok':
                    continue
                travel_time = data1['durations'][0][1]
                travel_distance = 0

                response = requests.get(
                    f'http://localhost:5000/route/v1/driving/{src_row["LOC_LONG"]},{src_row["LOC_LAT"]};{dst_row["LOC_LONG"]},{dst_row["LOC_LAT"]}?alternatives=false&steps=true&overview=full'
                )
                data2 = json.loads(response.text)
                if data2['code'] != 'Ok':
                    continue

                route = data2['routes'][0]
                scaled_waypoints = []
                waypoints = []
                for leg in route['legs']:
                    for step in leg['steps']:
                        for intersection in step['intersections']:
                            waypoint = intersection['location']
                            waypoints.append(f'{waypoint[0]}:{waypoint[1]}')
                            scaled_waypoint = ((waypoint[0] - long_base)/data_range, (waypoint[1] - lat_base)/data_range)
                            scaled_waypoints.append(f'{scaled_waypoint[0]}:{scaled_waypoint[1]}')

                entry = {
                    "SEED": args.seed,
                    "SRC_ID_UNIQUE": src_row['ID_UNIQUE'],
                    "SRC_INDEX": si,
                    "SRC_LOC_LONG": src_row['LOC_LONG'],
                    "SRC_LOC_LAT": src_row['LOC_LAT'],
                    "DST_ID_UNIQUE": dst_row['ID_UNIQUE'],
                    "DST_INDEX": di,
                    "DST_LOC_LONG": dst_row['LOC_LONG'],
                    "DST_LOC_LAT": src_row['LOC_LAT'],
                    "DISTANCE": travel_distance,
                    "TRAVEL_TIME": travel_time,
                    "WAYPOINTS": ';'.join(waypoints),
                    "SCALED_WAYPOINTS": ';'.join(scaled_waypoints),
                }

                distances.append(entry)

    return pd.DataFrame(distances)


def main(args):

    df = load_data(args)
    visualize(df)

    data, long_base, lat_base, data_range = cluster_data(args, df)
    visualize_clusters(data)
    output = ".".join([args.output, 'clustered', 'csv'])
    data.to_csv(output, index=False)

    plt.show(block=True)

    distance_data = collect_distance_data(args, data, long_base, lat_base, data_range)
    output = ".".join([args.output, 'distances', 'csv'])
    distance_data.to_csv(output, index=False)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description=__doc__)

    argparser.add_argument(
        '--input',
        default=None,
        type=str,
        help='Source CSV file')
    argparser.add_argument(
        '--output',
        default='taskdata',
        type=str,
        help='Source CSV file')
    argparser.add_argument(
        '--seed',
        default=42,
        type=int,
        help='Random seed for generation')
    argparser.add_argument(
        '--samples',
        default=10,
        type=int,
        help='Number of samples to draw')
    argparser.add_argument(
        '--clusters',
        default=2,
        type=int,
        help='Number of Clusters to create')

    args = argparser.parse_args()

    main(args)
