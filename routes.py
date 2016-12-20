#!/data/data/com.termux/files/usr/bin/python
# ^^^ special shebang line for termux

import sys, json, pprint
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from collections import Counter
from pybus import *

def get_all_ltadm_busroutes():
	return get_all_ltadm_obj("http://datamall2.mytransport.sg/ltaodataservice/BusRoutes")

def get_all_ltadm_busstops():
	return get_all_ltadm_obj("http://datamall2.mytransport.sg/ltaodataservice/BusStops")

def sort_busstops(s):
	'''Not really sorting...'''
	return {stop['BusStopCode']: stop for stop in s}

def sort_busroutes(s):
	'''Sort the bus routes by bus and route, and convert distances to integer values in metres.'''
	x = {}
	for entry in s:
		# convert distances to int metres
		try:
			entry["Distance"] = int(round(entry["Distance"] * 1000)) if entry["Distance"] is not None else None
		except TypeError:
			print("TypeError occured with this member of s: ")
			pprint.pprint(entry, indent=4)
			raise
		# then sort by bus and route ("sort" is a little misleading since dicts are unordered)
		if entry["ServiceNo"] not in x:
			x[entry["ServiceNo"]] = {}
		if entry["Direction"] not in x[entry["ServiceNo"]]:
			x[entry["ServiceNo"]][entry["Direction"]] = []
		x[entry["ServiceNo"]][entry["Direction"]].append(entry)
	return x

def check_busroutes(x):
	'''Check if the indexes within routes are consistent'''
	# omg it's a python pyramid!!!!1111!!1!
	ok = True
	for svc in x:
		for rt in x[svc]:
			has_bitched = False
			for i, v in enumerate(x[svc][rt]):
				if v["StopSequence"] != i + 1:
					if not has_bitched:
						print("Warning: StopSequence and list index mismatch at x['{0}'][{1}][{2}]['StopSequence'] is {3}, not {4}".format(svc, rt, i, v["StopSequence"], i+1))
						has_bitched = True
						ok = False
					else:
						print("Suppressing further warnings in x['{0}'][{1}]".format(svc, rt))
						break
	return ok

def bad_stops(all_stops):
	'''Find bad stops and report them'''
	# Rule 1: Description is Non Stop or Express
	desc_rule = [x["BusStopCode"] for x in all_stops.values() if x["Description"] in ["Non Stop", "Express"]]
	# Rule 2: Latitude/Longitude is 0
	assert([x for x in data_stops.values() if x["Latitude"] == 0] == [x for x in data_stops.values() if x["Longitude"] == 0])
	coords_rule = [x["BusStopCode"] for x in all_stops.values() if x["Latitude"] == 0]

	# combine (| meaning 'or'/union)
	return list(set(desc_rule) | set(coords_rule))
	
def duplicate_stops(all_routes, ignore_bad_stops=True, ignore_terminals=False):
	'''Find duplicate stops in each route and report them'''
	result = []
	for service_k, service in all_routes.items():
		for route_k, route in service.items():
			stop_codes = [stop['BusStopCode'] for stop in route]
			if ignore_bad_stops:
				stop_codes = [x for x in stop_codes if x not in data_bad_stops]
			cnt = Counter(stop_codes)
			dups = {k: v for k,v in cnt.items() if v > 1}
			if ignore_terminals:
				# is self assignment for comprehensions okay???
				dups = {k: v for k,v in dups.items() if k not in [stop_codes[0], stop_codes[-1]]}
			
			# ignore empty duplicate dicts
			if len(dups) == 0:
				continue
			
			result.append({
				"dups": dups,
				"service": service_k,
				"route": route_k
			})

	return result
	
def update_everything():
	'''Update everything.'''
	# download new data from LTADM
	print("Updating everything. This could take a while.")
	print("Getting routes...")
	routes_raw = get_all_ltadm_busroutes()
	print("Getting stops...")
	stops_raw = get_all_ltadm_busstops()
	
	print("Processing...")
	# munge it:
	stops = sort_busstops(stops_raw['data'])
	
	routes = sort_busroutes(routes_raw['data'])
	print("check_busroutes: " + check_busroutes(routes))
	
	bads = bad_stops(stops)
	duplicates = duplicate_stops(routes)
	
	with open("data_new/busstops.json", "w") as f:
		json.dump(stops, f, indent=2)
	
	with open("data_new/busroutes.json", "w") as f:
		json.dump(routes, f, indent=2)
	
	with open("data_new/bad_stops.json", "w") as f:
		json.dump(bads, f, indent=2)
		
	with open("data_new/duplicate_stops.json", "w") as f:
		json.dump(duplicates, f, indent=2)

def rt2dbgsrc(rt):
    '''Convert result of get_busroute_timing into something suitable for the debug_source arg of find_next_bus.'''
    pass

def main():
	usage = "usage: {0} -f path/to/outfile".format(sys.argv[0])
	if len(sys.argv) == 1:
		print(usage)
		quit()
	elif sys.argv[1] == "-f" and len(sys.argv) == 3:
		time_start = datetime.now()
		x = get_all_ltadm_busroutes()["data"]
		time_end = datetime.now()
		duration = time_end - time_start
		print("Response contains {0} entries and took {1} seconds".format(len(x), duration.total_seconds()))
		x = sort_busroutes(x) 
		if check_busroutes(x):
			print("Data looks ok.")
		with open(sys.argv[2], "w") as f:
			json.dump(x, f, indent=4)
		print("Wrote JSON data to {0}".format(sys.argv[2]))
	else:
		print(usage)

if __name__ == "__main__":
	main()
