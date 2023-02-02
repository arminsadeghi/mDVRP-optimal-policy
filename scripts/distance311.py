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
    sb.scatterplot(x=df['LOC_LAT'], y=df['LOC_LONG'])
    plt.show(block=True)


def collect_distance_data(args, df):

    distances = []

    df = df.reset_index()
    for si, src_row in df.iterrows():
        origin = (src_row['LOC_LAT'], src_row['LOC_LONG'])

        for di, dst_row in df.iterrows():
            dest = (dst_row['LOC_LAT'], dst_row['LOC_LONG'])

            # result = gmap.distance_matrix(origin, dest, mode = 'driving')
            # distance = result["rows"][0]["elements"][0]["distance"]["value"]
            # time = result["rows"][0]["elements"][0]["duration"]["value"]

            response = requests.get(
                f'http://localhost:5000/table/v1/driving/{src_row["LOC_LONG"]},{src_row["LOC_LAT"]};{dst_row["LOC_LONG"]},{dst_row["LOC_LAT"]}')
            data = json.loads(response.text)

            if data['code'] != 'Ok':
                continue

            print('----------------------------------------')
            print(data["destinations"][0])
            print(data["destinations"][1])
            print('     ----')
            print(data["sources"][0])
            print(data["sources"][1])
            print('     ----')
            print(data["durations"])

            travel_time = data['durations'][0][1]
            travel_distance = 0

            entry = {
                "SEED": args.seed,
                "SRC_ID_UNIQUE": src_row['ID_UNIQUE'],
                "SRC_INDEX": si,
                "SRC_LOC_LONG": src_row['LOC_LONG'],
                "SRC_LOC_LAT": src_row['LOC_LAT'],
                "DST_ID_UNIQUE": dst_row['ID_UNIQUE'],
                "SRC_INDEX": di,
                "DST_LOC_LONG": dst_row['LOC_LONG'],
                "DST_LOC_LAT": src_row['LOC_LAT'],
                "DISTANCE": travel_distance,
                "TRAVEL_TIME": travel_time,
            }

            distances.append(entry)

    return pd.DataFrame(distances)


def main(args):

    df = load_data(args)
    visualize(df)

    distance_data = collect_distance_data(args, df)
    output = ".".join(args.input.split('.')[:-1] + ['sampled_distances', 'csv'])
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
        '--seed',
        default=42,
        type=int,
        help='Random seed for generation')
    # argparser.add_argument(
    #     '--key',
    #     default=None,
    #     type=str,
    #     help='API key for Google Maps')
    argparser.add_argument(
        '--samples',
        default=2500,
        type=int,
        help='Number of samples to draw')

    args = argparser.parse_args()

    main(args)
