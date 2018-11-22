from de_lijn import DeLijn
from flask import jsonify

import requests


class Stops(DeLijn):
    def __init__(self, subscription_key, here_app_id, here_app_code):
        super().__init__(subscription_key, here_app_id, here_app_code)

    def stops_as_dict(self, province, line_number, direction):
        """ returns a dictionary containing the coordinates of the stops (key = stop number)"""
        try:
            direction = direction.upper()
            entity_number = self.get_entity_number(province)

            if (direction not in self.directions) or (line_number < 0) or (entity_number is None):
                return None

            url = self.DL_base_url + "lijnen/" \
                + str(entity_number) + "/" \
                + str(line_number) \
                + "/lijnrichtingen/" \
                + direction \
                + "/haltes"
            r = requests.get(url, headers=self.headers)

            if r.status_code != 200:
                return None
            stops = r.json()

            parameters = dict()

            for stop in stops["haltes"]:
                stop_info = dict()

                co = stop["geoCoordinaat"]
                stop_info["description"] = stop["omschrijving"]
                stop_info["coordinates"] = {"lat": co["latitude"], "lng": co["longitude"]}

                parameters[stop["haltenummer"]] = stop_info
            return parameters
        except ConnectionError:
            return None

    def get(self, province, line_number, direction):
        """ returns all stops for a bus/tram line and its information in json"""
        emtpy_json = jsonify({"stops": []})
        try:
            direction = direction.upper()
            entity_number = self.get_entity_number(province)

            if (direction not in self.directions) or (line_number < 0) or (entity_number is None):
                return emtpy_json

            url = self.DL_base_url + "lijnen/" \
                + str(entity_number) + "/" \
                + str(line_number) \
                + "/lijnrichtingen/" \
                + direction \
                + "/haltes"
            r = requests.get(url, headers=self.headers)

            if r.status_code != 200:
                return emtpy_json

            stops = r.json()

            parameters = list()

            # calculate weather for every town or city
            # balance between weather precision and performance
            weather = dict()

            for stop in stops["haltes"]:
                stop_info = dict()

                co = stop["geoCoordinaat"]
                town = stop["omschrijvingGemeente"]

                if town not in weather:
                    weather_url = "https://weather.cit.api.here.com/weather/1.0/report.json?app_id="
                    weather_url += self.here_app_id
                    weather_url += "&app_code="
                    weather_url += self.here_app_code
                    weather_url += "&product=observation"
                    weather_url += "&oneobservation=true"
                    weather_url += "&latitude="
                    weather_url += str(co["latitude"])
                    weather_url += "&longitude="
                    weather_url += str(co["longitude"])

                    r = requests.get(weather_url)

                    if r.status_code != 200:
                        continue
                    response = r.json()

                    weather[town] = response["observations"]["location"][0]["observation"][0]["description"]

                stop_info["coordinates"] = {"lat": co["latitude"], "lng": co["longitude"]}
                stop_info["description"] = stop["omschrijving"]
                stop_info["stopNumber"] = stop["haltenummer"]
                stop_info["weather"] = weather[town]

                parameters.append(stop_info)
            return jsonify({"stops": parameters})
        except Exception:
            return emtpy_json
