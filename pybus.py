#!/data/data/com.termux/files/usr/bin/python
# ^^^ special shebang line for termux

import sys
import json
import lxml.html
import re
import os
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from pprint import pprint

# API authorisation details (see LTA DataMall website)
with open("data/hdrs.json", "r") as f:
    hdrs = json.load(f)

hdrs["AccountKey"] = os.getenv("PYBUS_ACCOUNTKEY")
if hdrs['AccountKey'] == None:
    raise ValueError('Couldn\'t find $PYBUS_ACCOUNTKEY. Did you export it?')

# read in cached routes and stops
with open("data/busroutes.json", "r") as f:
    data_routes = json.load(f)

with open("data/busstops.json", "r") as f:
    data_stops = json.load(f) 

print("Loaded cached data")

def get_bus_arr(BusStopID, ServiceNo):
    url = "http://datamall2.mytransport.sg/ltaodataservice/BusArrival?BusStopID={0}&ServiceNo={1}".format(BusStopID, ServiceNo)
    #print(url)
    return get_ltadm_obj(url)

def write_bus_arr(BusStopID, ServiceNo):
    x = get_bus_arr(BusStopID, ServiceNo)
    fname = "busarr-{0}-{1}.json".format(BusStopID, ServiceNo)
    
    with open(fname, "w") as f:
        json.dump(x, f, indent=4)
    
    print("Wrote response to " + fname)
    return

def get_ltadm_obj(url):
    '''Fetch JSON data from an LTA DataMall endpoint and decode it, inserting a timestamp before returning the object'''
    # look out for HTTPError or json.decoder.JSONDecodeError
    rq = Request(url, headers = hdrs)
    
    resp = urlopen(rq).read().decode("utf-8")
    x = json.loads(resp)
    # add a timestamp
    x["request_time"] = str(datetime.utcnow())
    
    return x

def get_ltadm_obj_skip(url, skip = 0):
    '''Fetch JSON data from an LTA DataMall endpoint and decode it. skip is the parameter for $skip (see the LTA DataMall documentation for more info)'''
    if len(url.split("?")) > 1:
        # there is at least one ? token in the url
        fstr = "{0}&$skip={1}"
    else:
        fstr = "{0}?$skip={1}"
    url = fstr.format(url, skip)
    return get_ltadm_obj(url) 

def get_all_ltadm_obj(url):
    '''Fetch all LTA DataMall data from an endpoint that implements the $skip parameter.'''
    time_start = str(datetime.now())
    skip = 0
    # req_len is the max number of data items per request
    req_len = 50
    x = []
    while True:
        y = get_ltadm_obj_skip(url, skip)["value"]
        x += y
        if len(y) < req_len:
            break
        skip += 50
    time_end = str(datetime.now())
    return {"data": x, "time_start": time_start, "time_end": time_end} 

def utc2dt(utcstr):
    '''Convert UTC time to a datetime object'''
    if utcstr == "":
        return
    if utcstr[-6:] != "+00:00":
        raise TypeError("Bad timezone in " + utcstr)
    utcstr = utcstr[:-6]
    dt = datetime.strptime(utcstr, "%Y-%m-%dT%H:%M:%S")
    return dt

def get_busroute_timing_iter(bus, stops):
# this uses yield instead of making every request at once to let the user control the rate of requests. LTA DataMall doesn't have a published API limit but that might change in the future
    try:
        for stop in stops:
            resp = get_bus_arr(stop, bus)
            service = resp["Services"][0]
            yield [service["NextBus"]["EstimatedArrival"], service["SubsequentBus"]["EstimatedArrival"], service["SubsequentBus3"]["EstimatedArrival"]]
    except IndexError as e:
        print("IndexError in stop={0} bus={1}".format(stop, bus))
        raise

def get_busroute_timing(bus, stops, descs):
    keys = ["stop", "desc", "timings"]
    timings = [t for t in get_busroute_timing_iter(bus, stops)]
    return {"data": [dict(zip(keys, x)) for x in zip(stops, descs, timings)], "request_time": datetime.utcnow()}

def get_rt_cached(ServiceNo, RouteNo):
    '''Get bus arrival timings (in seconds from request time) using the cached routes'''
    # route = routes["ServiceNo"]["RouteNo"]
    route = data_routes.get(str(ServiceNo), {}).get(str(RouteNo), {})
    stops = [stop["BusStopCode"] for stop in route]
    descs = [data_stops[str(stop)]["Description"] for stop in stops]
    rt = get_busroute_timing(ServiceNo, stops, descs)
    rt.update(service=str(ServiceNo), route_index=str(RouteNo))

    # use a list comp for this?
    for stop_i, stop in enumerate(rt["data"]): 
        for timing_i, timing in enumerate(rt["data"][stop_i]["timings"]):
            rt["data"][stop_i]["timings"][timing_i] = int((utc2dt(timing) - rt["request_time"]).total_seconds()) if timing is not "" else None
    return rt

def stop_distance(ServiceNo, RouteIndex, Stop1, Stop2):
    '''Find the distance in stops between two stops on the same route. Returns a positive int if Stop2 > Stop1.'''
    route = data_routes.get(str(ServiceNo), {}).get(str(RouteIndex), {})
    stops = [stop["BusStopCode"] for stop in route]
    return stops.index(str(Stop2)) - stops.index(str(Stop1))

def interpolate_rt(route):
    '''Interpolate missing route timings using distance between stops.'''
    pass

def find_next_bus(rt, stop_id):
    '''Find the next bus approaching stop. If a bus is found then this function returns a dict containing the stop id of the stop before the bus ("stop") and its index in the route ("stop_index").'''
    # find the member of the rt list corresponding to stop_id
    try:
        stop_index = next((k for k,v in enumerate(rt["data"]) if v["stop"] == str(stop_id)))
    except StopIteration:
        return

    # work backwards and find the first stop with a bus less than 60 seconds away (this is what LTA says the "Arr" indication means) 
    distance = 60
    while stop_index > 0:
        # if (rt["data"][stop_index]["timings"][0] - rt["request_time"]).total_seconds() < distance:
        if rt["data"][stop_index]["timings"][0] < distance:
            return {
                "stop": rt["data"][stop_index]["stop"],
                "stop_index": stop_index,
                "stop_distance": stop_distance(rt["service"], rt["route_index"], rt["data"][stop_index]["stop"], stop_id)
            }
        else:
            stop_index -= 1
    return None

def route_ends(service, route_index):
    '''Get details about the two ends of the given route.'''
    route = data_routes.get(str(service), {}).get(str(route_index), {})
    if route == {}:
        return None
    else:
        return {"first_stop": data_stops.get(route[0]["BusStopCode"], {}), "last_stop": data_stops.get(route[-1]["BusStopCode"], {})}
    

def main():
    if len(sys.argv) < 2:
        print("Try -b or -r or -f")
    elif sys.argv[1] == "-b":
        if len(sys.argv) != 4:
            print("Get time to arrival of next bus.")
            print("usage: " + sys.argv[0] + " -b BusStopID ServiceNo")
            quit()
        pprint(get_bus_arr(*sys.argv[2:]), indent=4)
    elif sys.argv[1] == "-r":
        if len(sys.argv) != 4:
            print("Get bus route.")
            print("usage: " + sys.argv[0] + "-r ServiceNo RouteIndex")
            quit()
        try:
            pprint(get_rt_cached(*sys.argv[2:]), indent=4)
        except IndexError:
            print("IndexError, check RouteIndex")
    elif sys.argv[1] == "-f":
        if len(sys.argv) != 5:
            print("Find next bus approaching stop.")
            print("usage:" + sys.argv[0] + "-f ServiceNo RouteIndex BusStopID")
            quit()
        pprint(find_next_bus(get_rt_cached(*sys.argv[2:4]), sys.argv[4]), indent=4)

if __name__ == "__main__":
    # run as script
    main()

