# pybus

A service for finding buses around a stop in Singapore. Runs on Python 3 and Flask.

A deployment of this app lives at <http://pybus-sg.herokuapp.com/>.

## Setting up

Clone and install requirements:

    $ git clone https://github.com/nik0sc/pybus.git
    $ cd pybus
    $ virtualenv .      # (if you want)
    $ pip install -r requirements.txt

Next, you will need an API key from [LTA DataMall](https://www.mytransport.sg/content/mytransport/home/dataMall.html). Create an environment variable named `PYBUS_ACCOUNTKEY` containing this key, like so:

    $ export PYBUS_ACCOUNTKEY=<your_key_here>

Or, roll your own startup script. Idea for a name: `runapp` is included in the root `.gitignore`.

## To start

    $ export FLASK_APP=pbapp.py
    $ flask run

The `pbapp.app` object is a WSGI app; you can plug it into any server that understands it (apache, nginx, gunicorn, etc) if you don't want to use the builtin Flask server.

## Endpoints

Once Flask is up and running, you can access pybus's endpoints on `localhost:5000` by default. All the endpoints return JSON data (except `/`).

### `/services`

A naturally sorted list of all bus service numbers.

### `/routes/<service>`

The starting and ending stops of all routes under the bus `<service>`.

### `/route_ends/<service>/<route_index>`

Like `/routes/<service>` but only for one route.

### `/stops/<service>/<route>`

All the stops along a bus route, in order.

### `/find_bus/<service>/<route_index>/<stop_id>`

Location of the nearest bus on the way to `<stop_id>`.

### `/find_bus_extra/<service>/<route_index>/<stop_id>`

Like `/find_bus/...` but also returns all the stops (codes, descriptions and coordinates) between the bus and `<stop_id>`.

## Notes

The idea for this came from the SG BusLeh app. This is basically a reimplementation of their bus locator function. Yes, SG BusLeh is prior art, and no I do not claim that this is an original idea. However, all code is original.

