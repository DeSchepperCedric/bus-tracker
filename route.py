from de_lijn import DeLijn
from flask import jsonify

import requests


class Route(DeLijn):
    def __init__(self, subscription_key, here_app_id, here_app_code):
        super().__init__(subscription_key, here_app_id, here_app_code)

    def get(self, province, line_number, direction="HEEN"):
        """ returns the routing parameters for a bus/tram line"""
        empty_json = jsonify({"parameters": dict()})
        try:
            entity_number = self.get_entity_number(province)
            if (line_number < 0) or (direction not in self.directions) or (entity_number is None):
                return empty_json

            url = self.DL_base_url + "lijnen/" \
                + str(entity_number) + "/" \
                + str(line_number) \
                + "/lijnrichtingen/" \
                + direction \
                + "/haltes"

            r = requests.get(url, headers=self.headers)

            if r.status_code != 200:
                return empty_json
            stops = r.json()

            parameters = dict()
            parameters["mode"] = "fastest;publicTransport;traffic:disabled"
            parameters["representation"] = "display"
            parameters["routeattributes"] = "waypoints"
            parameters["maneuverattributes"] = "direction,action"
            number = 0
            for stop in stops["haltes"]:
                co = stop["geoCoordinaat"]
                parameters["waypoint" + str(number)] = "geo!" + str(co["latitude"]) + "," + str(co["longitude"])
                number += 1
            return jsonify({"parameters": parameters})
        except Exception:
            return empty_json
