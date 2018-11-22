from flask_restful import Resource

import requests

"""
API by De Lijn found at https://data.delijn.be/
"""


class DeLijn(Resource):

    def __init__(self, subscription_key, here_app_id, here_app_code):
        self.subscription_key = subscription_key
        self.headers = {"Ocp-Apim-Subscription-Key": self.subscription_key}

        self.DL_base_url = "https://delijn.azure-api.net/DLKernOpenData/v1/beta/"
        self.directions = ["HEEN", "TERUG"]

        self.here_app_id = here_app_id
        self.here_app_code = here_app_code

    def get_entity_number(self, province):
        """ returns entity number of a province"""
        province = "-".join(w.capitalize() for w in province.split("-"))
        url = self.DL_base_url + "/entiteiten"
        r = requests.get(url, headers=self.headers)
        if r.status_code == 404:
            return None
        entities = r.json()

        for element in entities["entiteiten"]:
            if element["omschrijving"] == province:
                return element["entiteitnummer"]
