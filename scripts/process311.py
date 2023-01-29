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

ORIGINAL_DATATYPES = {
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
    "PROVENANCE_ORIGINALE": str,
    "PROVENANCE_TELEPHONE": str,
    "PROVENANCE_COURRIEL": str,
    "PROVENANCE_PERSONNE": str,
    "PROVENANCE_COURRIER": str,
    "PROVENANCE_TELECOPIEUR": str,
    "PROVENANCE_INSTANCE": str,
    "PROVENANCE_MOBILE": str,
    "PROVENANCE_MEDIASOCIAUX": str,
    "PROVENANCE_SITEINTERNET": str,
    "UNITE_RESP_PARENT": str,
    "LOC_LONG": np.float64,
    "LOC_LAT": np.float64,
    "LOC_X": np.float64,
    "LOC_Y": np.float64,
    "DERNIER_STATUT": str,
    "DATE_DERNIER_STATUT": str,
}

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
    df = pd.read_csv(args.input, dtype=ORIGINAL_DATATYPES)

    df = df[FILTERED_COLUMNS]
    df = df.loc[(df['NATURE'] == NATURE_OF_SERVICE) & (df['ARRONDISSEMENT_GEO'] == BOROUGH_OF_SERVICE)]
    df = df.reset_index()

    output = ".".join(args.input.split('.')[:-1] + ['filtered', 'csv'])
    df.to_csv(output, index=False)


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
