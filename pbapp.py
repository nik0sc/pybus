#!/data/data/com.termux/files/usr/bin/python
# ^^^ special shebang line for termux

import pybus
import json
from natsort import natsorted
from flask import Flask
app = Flask(__name__)

@app.route("/find_bus/<service>/<route_index>/<stop_id>")
def find_bus(service, route_index, stop_id):
    # return json.dumps(pybus.find_next_bus(pybus.get_rt_cached(service, route_index), stop_id))
    # WARNING! The structure of the returned object has changed!
    return json.dumps(pybus.find_next_bus_efficient(service, route_index, stop_id)[0])

@app.route("/route_ends/<service>/<route_index>")
def route_ends(service, route_index):
    return json.dumps(pybus.route_ends(service, route_index))

@app.route("/services")
def get_services():
    return json.dumps(list(natsorted(pybus.data_routes.keys())))

@app.route("/routes/<service>")
def get_routes(service):
    routes = {}
    for k in pybus.data_routes.get(service, {}):
        routes[k] = pybus.route_ends(service, k)
    return json.dumps(routes)

@app.route("/stops/<service>/<route>")
def get_stops(service, route):
    stop_nos = [x["BusStopCode"] for x in pybus.data_routes.get(service, {}).get(route, {})]
    # stop_descs = [pybus.data_stops.get(x, {}).get("Description", "") for x in stop_nos]
    stops = [pybus.data_stops.get(x, {}) for x in stop_nos]
    return json.dumps(stops)
    

# statics
@app.route("/<path:path>")
def static_file(path):
    return app.send_static_file(path)

if __name__ == "__main__":
    app.run(debug=True)

