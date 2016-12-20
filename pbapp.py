#!/data/data/com.termux/files/usr/bin/python
# ^^^ special shebang line for termux

import pybus
import json
import os
from natsort import natsorted
from flask import Flask, render_template
app = Flask(__name__)

# some globals
#with open("commithash", "r") as f:
#    commit_hash = f.read()

commit_hash = os.getenv("HEROKU_SLUG_DESCRIPTION")
heroku_release_version = os.getenv("HEROKU_RELEASE_VERSION")

@app.route("/find_bus/<service>/<route_index>/<stop_id>")
def find_bus(service, route_index, stop_id):
    # return json.dumps(pybus.find_next_bus(pybus.get_rt_cached(service, route_index), stop_id))
    # WARNING! The structure of the returned object has changed!
    return json.dumps(pybus.find_next_bus(service, route_index, stop_id)[0])

@app.route("/find_bus_extra/<service>/<route_index>/<stop_id>")
def find_bus_extra(service, route_index, stop_id):
    try:
        res = pybus.find_next_bus(service, route_index, stop_id)
    except ValueError as e:
        return json.dumps({"error": "stop not in route"}), 500
    except RuntimeError as e:
        return json.dumps({"error": "no bus timings available"}), 500
    except Exception as e:
        # return json.dumps({"error": "other exception {0}".format(repr(e))}), 500
        raise

    return json.dumps({"next_bus": res[0], "rt": res[1]})

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
    stop_nos = [x["BusStopCode"] for x in pybus.data_routes.get(service, {}).get(route, {}) if x["BusStopCode"] not in pybus.data_bad_stops]
    # stop_descs = [pybus.data_stops.get(x, {}).get("Description", "") for x in stop_nos]
    stops = [pybus.data_stops.get(x, {}) for x in stop_nos]
    return json.dumps(stops)
    
@app.route("/")
@app.route("/index.html")
def index():
    return render_template("index.html",
        commit_hash=commit_hash,
        heroku_release_version=heroku_release_version,
        services=list(natsorted(pybus.data_routes.keys()))
    )

# statics
@app.route("/<path:path>")
def static_file(path):
    return app.send_static_file(path)

if __name__ == "__main__":
    app.run(debug=True)

