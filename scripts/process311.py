#
# A short script to parse the data from the Montreal 2017-2019 311 data set and extract the service requests that
# include the lat/log as  location data
#
# Data set can be found at: https://open.canada.ca/data/en/dataset/5866f832-676d-4b07-be6a-e99c21eb17e4
#

import pandas as pd
import argparse
import numpy as np

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

NATURE_OF_SERVICE = 'Requete'
BOROUGH_OF_SERVICE = 'Montréal-Nord'


def parse(args):
    df = pd.read_csv(args.input)

    df = df[FILTERED_COLUMNS]
    df = df.loc[(df['NATURE'] == NATURE_OF_SERVICE) & (df['ARRONDISSEMENT_GEO'] == BOROUGH_OF_SERVICE)]
    output = ".".join(args.input.split('.')[:-1] + ['filtered', 'csv'])
    df.to_csv(output)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description=__doc__)

    argparser.add_argument(
        '--input',
        default=None,
        type=str,
        help='Source CSV file')

    args = argparser.parse_args()

    parse(args)
