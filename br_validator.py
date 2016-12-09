#!/bin/python3
import requests
from pprint import pprint

def stops_from_busrouter(service, rt_to_test):
    """rt_to_test is a pybus dict containing a single rt.
    service is a string (important), the service to test."""
    req = requests.get('https://busrouter.sg/data/2/bus-services/{0}.json'.format(service))
    if req.status_code != '200':
        throw ValueError('Service {0} not in busrouter data'.format('service'))
    
    br_rts = req.json()

    # try and find the route automatically

    for br_rt in br_rts:
        if rt_to_test[0]["BusStopCode"] == br_rt["stops"][0]:
            # continue later
