#!/data/data/com.termux/files/usr/bin/python
# ^^^ special shebang line for termux

import sys
import json
# import lxml.html
import re
import os
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from pprint import pprint
from collections import Counter

# API authorisation details (see LTA DataMall website)
with open("data/hdrs.json", "r") as f:
    hdrs = json.load(f)

hdrs["AccountKey"] = os.getenv("PYBUS_ACCOUNTKEY")
if hdrs['AccountKey'] == None:
    raise ValueError('Couldn\'t find $PYBUS_ACCOUNTKEY. Did you export it?')

# read in cached routes and stops
# don't modify these globals. NOTE x = dict.get(); x.reverse() will modify the source dict!!
with open("data/busroutes.json", "r") as f:
    data_routes = json.load(f)

with open("data/busstops.json", "r") as f:
    data_stops = json.load(f) 

with open("data/bad_stops.json", "r") as f:
    # http://stackoverflow.com/questions/2831212/python-sets-vs-lists
    data_bad_stops = frozenset(json.load(f))

print("Loaded cached data")

def get_ltadm_obj(url, timestamp=True):
    '''Fetch JSON data from an LTA DataMall endpoint and decode it, inserting a timestamp before eeturning the object. This is the lowest-level function that gets LTADM data.'''
    # look out for HTTPError or json.decoder.JSONDecodeError
    rq = Request(url, headers = hdrs)
    
    resp = urlopen(rq).read().decode("utf-8")
    x = json.loads(resp)
    if timestamp == True:
        x["request_time"] = datetime.utcnow()
    
    return x

def get_ltadm_obj_skip(url, skip=0, timestamp=True):
    '''Fetch JSON data from an LTA DataMall endpoint and decode it. skip is the parameter for $skip (see the LTA DataMall documentation for more info)'''
    if len(url.split("?")) > 1:
        # there is at least one ? token in the url
        fstr = "{0}&$skip={1}"
    else:
        fstr = "{0}?$skip={1}"
    url = fstr.format(url, skip)
    return get_ltadm_obj(url, timestamp) 

def get_all_ltadm_obj(url):
    '''Fetch all LTA DataMall data from an endpoint that implements the $skip parameter.'''
    # over here time_start and _end are strings, but get_ltadm_obj()["request_time"] is a datetime object, because this function's output is likely to be written to a file. In contrast, get_ltadm_obj()'s output and functions that use it, will store the result in memory only, or will not write the request_time member to a file or string.
    time_start = str(datetime.now())
    skip = 0
    # req_len is the max number of data items per request
    req_len = 50
    x = []
    while True:
        y = get_ltadm_obj_skip(url, skip, timestamp=False)["value"]
        x += y
        if len(y) < req_len:
            break
        skip += 50
    time_end = str(datetime.now())
    return {"data": x, "time_start": time_start, "time_end": time_end} 

def get_bus_arr(BusStopID, ServiceNo):
    '''Get an LTA DataMall bus arrival object. This is a specialised version of get_ltadm_obj().'''
    url = "http://datamall2.mytransport.sg/ltaodataservice/BusArrival?BusStopID={0}&ServiceNo={1}".format(BusStopID, ServiceNo)
    #print(url)
    return get_ltadm_obj(url)

def write_bus_arr(BusStopID, ServiceNo):
    '''Utility and testing function: write out an LTA DataMall bus arrival object to a file'''
    x = get_bus_arr(BusStopID, ServiceNo)
    x["request_time"] = str(x["request_time"])
    fname = "busarr-{0}-{1}.json".format(BusStopID, ServiceNo)
    
    with open(fname, "w") as f:
        json.dump(x, f, indent=4)
    
    print("Wrote response to " + fname)
    return

def utc2dt(utcstr):
    '''Convert UTC time to a datetime object'''
    if utcstr == "":
        return None
    if utcstr[-6:] != "+00:00":
        raise TypeError("Bad timezone in " + utcstr)
    utcstr = utcstr[:-6]
    dt = datetime.strptime(utcstr, "%Y-%m-%dT%H:%M:%S")
    return dt

def get_busroute_timing_iter(bus, stops):
    '''Return an iterator that fetches the bus arrival timing in seconds for each stop in stops.'''
    # this uses yield instead of making every request at once to let the user control the rate of requests. LTA DataMall doesn't have a published API limit but that might change in the future
    # ... also, heroku chokes if you make this many requests in a row
    try:
        for stop in stops:
            resp = get_bus_arr(stop, bus)
            if not resp["Services"]:
                yield {
                    "stop": stop,
                    "timings": [],
                }

            service = resp["Services"][0]
            timings = [
                service["NextBus"]["EstimatedArrival"],
                service["SubsequentBus"]["EstimatedArrival"],
                service["SubsequentBus3"]["EstimatedArrival"]
            ]
            # SyntaxError if you switch the for and if/else clauses around
            timings_secs = [int((utc2dt(x) - resp["request_time"]).total_seconds()) if x != "" else None for x in timings]
            yield {
                "timings": timings_secs,
                "stop": stop
            }

    except IndexError as e:
        print("IndexError in stop={0} bus={1}".format(stop, bus))
        raise

def get_busroute_timing(bus, stops, descs):
    keys = ["stop", "desc", "timings"]
    timings = [t["timings"] for t in get_busroute_timing_iter(bus, stops)]
    return {
        # how did I even write this??? probably the hardest bit of code in here
        "data": [dict(zip(keys, x)) for x in zip(stops, descs, timings)],
        "request_time": datetime.utcnow()
    }

def get_rt_cached(service, route_index):
    '''Get bus arrival timings (in seconds from request time) using the cached routes'''
    # TODO: verify that this still works as normal
    route = data_routes.get(str(service), {}).get(str(route_index), {})
    stops = [stop["BusStopCode"] for stop in route]
    descs = [data_stops[str(stop)]["Description"] for stop in stops]
    
    rt = get_busroute_timing(service, stops, descs)
    rt.update(service=str(service), route_index=str(route_index))
    return rt

def stop_distance(service, route_index, stop1, stop2):
    '''Find the distance in stops between two stops on the same route. Returns a positive int if stop2 is after stop1 in the specified route.'''
    route = data_routes.get(str(service), {}).get(str(route_index), {})
    stops = [stop["BusStopCode"] for stop in route]
    return stops.index(str(stop2)) - stops.index(str(stop1))

def interpolate_rt(route):
    '''Interpolate missing route timings using distance between stops.'''
    pass
    
def find_duplicate_stop(stop_codes, stop_id):
    '''Check if stop_id occurs more than once in stop_codes.'''
    cnt = Counter(stop_codes)
    return cnt[stop_id] > 1

def find_next_bus(service, route_index, stop_id, debug_source=None):
    '''Find the location of the next bus approaching stop_id.'''
    # TODO implement hook for debug_source
    # directly corresponds to /find_bus/<service>/...
    # first, get the route...
    route = data_routes.get(str(service), {}).get(str(route_index), {}).copy()
    # search backwards from the given stop
    route.reverse()

    stop_codes = [stop["BusStopCode"] for stop in route if stop["BusStopCode"] not in data_bad_stops]
    
    try:
        stop_first_index = stop_codes.index(stop_id)
    except ValueError:
        raise ValueError("Stop not in route: service={0} route_index={1} stop_id={2}".format(service, route_index, stop_id))

    # check for duplicate stop_id
    is_duplicate = find_duplicate_stop(stop_codes, stop_id)
    
    # truncate working data
    route = route[stop_first_index:]
    stop_codes = stop_codes[stop_first_index:]
    
    # cached stop data
    stop_gen = (data_stops[str(stop_code)] for stop_code in stop_codes)
    
    # remember, this is in reverse
    rt = []
    found = None
    method_used = None
    threshold = 60
    source = debug_source if debug_source is not None else get_busroute_timing_iter(service, stop_codes)
    for stop_timing in source:
        data_stop = next(stop_gen)
        stop_timing.update(
            desc=data_stop["Description"],
            lat=data_stop["Latitude"],
            lng=data_stop["Longitude"]
        )
        rt.append(stop_timing)
        if not stop_timing["timings"] or not stop_timing["timings"][0]:
            raise RuntimeError("No timings available")
        if stop_timing["timings"][0] < threshold:
            found = rt[-1]["stop"]
            method_used = "threshold"
            break
        
        cur_index = rt.index(stop_timing)
        if cur_index == 0:
            continue
        elif rt[cur_index]["timings"][0] > rt[cur_index - 1]["timings"][0]:
            found = rt[-2]["stop"]
            method_used = "jump"
            break
        
    # TODO: then if the converted time is less than threshold OR it suddenly jumps backward, note it as the location of the next bus
    return {
        "stop": found,
        # "stop_index": rt[-2][,
        # badly named variables!
        "stop_distance": stop_distance(service, route_index, found, stop_id),
        "method_used": method_used,
        "desc": rt[-1]["desc"],
        "duplicate": is_duplicate
    }, rt
         

def route_ends(service, route_index):
    '''Get details about the two ends of the given route.'''
    route = data_routes.get(str(service), {}).get(str(route_index), {})
    if route == {}:
        return None
    else:
        return {
            "first_stop": data_stops.get(route[0]["BusStopCode"], {}),
            "last_stop": data_stops.get(route[-1]["BusStopCode"], {})
        }
    

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
        pprint(find_next_bus(*sys.argv[2:5]), indent=4)

if __name__ == "__main__":
    # run as script
    main()

