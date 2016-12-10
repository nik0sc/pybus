#!/usr/bin/env python3
import requests
import sys
import json

def stops_from_busrouter(service, rt_to_test):
    """rt_to_test is a pybus dict containing a single rt.
    service is a string (important), the service to test.
    Returns true if the stops match
    All apologies to the creator of busrouter.sg"""
   
    req = requests.get('https://busrouter.sg/data/2/bus-services/{0}.json'.format(service))
    if req.status_code != 200:
        raise ValueError('Service {0} not in busrouter data'.format(service))
    
    br_rts = req.json()

    # try and find the route automatically

    for br_rt in br_rts.values():
        if br_rt == {'route': [], 'stops': []}:
            # empty route (probably this is a feeder service or runs in a big loop)
            continue
        if rt_to_test[0]['BusStopCode'] == br_rt['stops'][0]:
            rt_munged = [x['BusStopCode'] for x in rt_to_test]
            if rt_munged == br_rt['stops']:
                # yes, equality test for lists works by each element
                    return True

    return False

def scrape_busrouter(all_routes):
    """Compare each route in the all_routes dict with its busrouter counterpart, returning which routes passed and which are different.
    Don't do this too often, don't want to eat all of busrouter's bandwidth"""
    good = []
    bad = []
    ugly = []
    # route_repr = lambda x: '{0}/{1}'.format(x[0]['ServiceNo'], x[0]['Direction'])

    for service in all_routes:
        for route in all_routes[service]:
            route_code = '{0}/{1}'.format(service, route)
            print('Testing {0}.....'.format(route_code), end='')
            try:
                if stops_from_busrouter(service, all_routes[service][route]):
                    good.append(route_code)
                    print('good')
                else:
                    bad.append(route_code)
                    print('bad')
            except ValueError as e:
                print('got ValueError')
                ugly.append(route_code)

    return {'good': good, 'bad': bad, 'ugly': ugly}

def main():
    with open('data/busroutes.json') as f:
        all_routes = json.load(f)
    result = scrape_busrouter(all_routes)
    with open('data/br_validator_result.json', 'w') as f:
        json.dump(result, f, indent=4)

if __name__ == '__main__':
    main()


