from de_lijn import DeLijn
from stops import Stops
from flask import jsonify

import requests
import datetime


class Buses(DeLijn):
    def __init__(self, subscription_key, here_app_id, here_app_code):
        super().__init__(subscription_key, here_app_id, here_app_code)

    @staticmethod
    def calculate_date_time(time_string):
        """ returns datetime of a time string given by DeLijn"""
        date_and_time = time_string.split("T")
        date = date_and_time[0].split("-")
        time = date_and_time[1].split(":")
        stop_time = datetime.datetime(int(date[0]), int(date[1]), int(date[2]),
                                      int(time[0]), int(time[1]), int(time[2]))

        return stop_time

    def get(self, province, line_number, direction):
        """ returns all buses and its information for a bus/tram line in json"""
        emtpy_json = jsonify({"buses": []})
        try:

            direction = direction.upper()
            entity_number = self.get_entity_number(province)

            if (direction not in self.directions) or (line_number < 0) or (entity_number is None):
                return emtpy_json

            #
            # calculate where bus is between its two stops
            #
            url = self.DL_base_url + "lijnen/" \
                + str(entity_number) + "/" \
                + str(line_number) \
                + "/lijnrichtingen/" \
                + direction \
                + "/dienstregelingen"
            r = requests.get(url, headers=self.headers)

            if r.status_code == 404:
                return None
            buses = r.json()

            current_time = datetime.datetime.now()

            stops_dict = Stops(subscription_key=self.subscription_key,
                               here_app_id=self.here_app_id,
                               here_app_code=self.here_app_code).stops_as_dict(province, line_number, direction)
            if stops_dict is None:
                return emtpy_json
            bus_parameters = list()
            for bus in buses["ritDoorkomsten"]:
                bus_number = bus["ritnummer"]

                prev_stop_index = 0
                next_stop_index = 0

                prev_stop_time = None
                next_stop_time = None

                last_index = 0
                first = True
                for i in range(0, len(bus["doorkomsten"])):
                    stop = bus["doorkomsten"][i]
                    # no time value: skip
                    if "dienstregelingTijdstip" not in stop:
                        continue
                    stop_time = self.calculate_date_time(stop["dienstregelingTijdstip"])
                    last_index = i

                    # bus still needs to leave terminal
                    if first is True and stop_time > current_time:
                        break

                    if stop_time < current_time:
                        prev_stop_index = i
                        prev_stop_time = stop_time

                    else:
                        next_stop_index = i
                        next_stop_time = stop_time
                        break
                    first = False

                prev_stop_number = bus["doorkomsten"][prev_stop_index]["haltenummer"]
                next_stop_number = bus["doorkomsten"][next_stop_index]["haltenummer"]

                if prev_stop_index == last_index:
                    continue
                if prev_stop_number == next_stop_number:
                    continue

                waypoint0 = str(stops_dict[prev_stop_number]["coordinates"]["lat"]) + "," \
                    + str(stops_dict[prev_stop_number]["coordinates"]["lng"])

                waypoint1 = str(stops_dict[next_stop_number]["coordinates"]["lat"]) + "," \
                    + str(stops_dict[next_stop_number]["coordinates"]["lng"])

                route_url = "https://route.api.here.com/routing/7.2/calculateroute.json?app_id="
                route_url += self.here_app_id
                route_url += "&app_code="
                route_url += self.here_app_code
                route_url += "&waypoint0=geo!"
                route_url += waypoint0
                route_url += "&waypoint1=geo!"
                route_url += waypoint1
                route_url += "&mode=fastest;publicTransport;traffic:disabled"

                r = requests.get(route_url)

                if r.status_code != 200:
                    continue
                response = r.json()
                maneuver = response["response"]["route"][0]["leg"][0]["maneuver"]
                travel_times = list()
                travel_stops = list()
                first = True
                for element in maneuver:
                    if first:
                        travel_times.append(element["travelTime"])

                        first = False
                    else:
                        travel_times.append(travel_times[len(travel_times) - 1] + element["travelTime"])
                    travel_stops.append(element["position"])

                total_stop_difference = (next_stop_time - prev_stop_time).total_seconds()

                second_penalty = float(travel_times[len(travel_times) - 1]) / total_stop_difference
                time_passed = (current_time - prev_stop_time).total_seconds() * second_penalty
                location_index = 0
                for element in travel_times:
                    if element > time_passed:
                        bus = dict()
                        bus["coordinates"] = {"lat": travel_stops[location_index]["latitude"],
                                              "lng": travel_stops[location_index]["longitude"]}
                        bus["number"] = bus_number
                        bus["nextStop"] = stops_dict[next_stop_number]["description"]
                        bus_parameters.append(bus)
                        break
                    location_index += 1

            return jsonify({"buses": bus_parameters})
        except Exception:
            return emtpy_json
