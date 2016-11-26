
def get_busroute_html(bus):
	url = "http://www.mytransport.sg/content/mytransport/ajax_lib/map_ajaxlib.getBusRouteByServiceId.{0}.html".format(bus)
	return urlopen(url).read().decode("utf-8")

def write_busroute_html(bus):
	resp = get_busroute_html(bus)
	fname = "busroute-{0}.html".format(bus)
	with open(fname, "w") as f:
		f.write(resp)

def get_busroute_urls(bus):
	page = get_busroute_html(bus)
	doc = lxml.html.fromstring(page)
	infos = doc.xpath('//a[@class="route_info_icon"]/@onclick')
	paths_root = "https://www.mytransport.sg"
	paths = list(map(lambda x: paths_root + re.findall('"([^"]*)"', x)[0], infos))
	return paths

def get_busroute_stops(path):
	resp = urlopen(path).read().decode("utf-8")
	doc = lxml.html.fromstring(resp)
# there's a normal_version and a print_version
	stops = doc.xpath('//div[@id="normal_version"]//div[@class="main_col_bus_stop_code green_colored"]/text()')
# also the class of the enclosing div of stop names can be either ...text_long or ...text_short depending on whether there is an icon next to it
	descs = doc.xpath('//div[@id="normal_version"]//div[starts-with(@class, "main_col_bus_stop_description_text_")]/text()')
	return stops, descs

