import re
import sys
import json
import logging
import requests
import urllib.parse
from bs4 import BeautifulSoup


logging.basicConfig(level=logging.INFO)

domain = 'https://www.beeradvocate.com/'
places_rel_url = 'place/list/'
places_url = urllib.parse.urljoin(domain, places_rel_url)
places_params = {'start': 0, 'brewery': 'Y', 'sort': 'name'}

def parse_breweries():	
	next_page_start = 0
	has_next = True
	links = []
	while has_next:
		params = places_params.copy()
		params['start'] = next_page_start
		logging.debug("parse_breweries: fetching page with start {}".format(next_page_start))		

		response = requests.get(url=places_url, params=params)
		soup = BeautifulSoup(response.text, features='lxml')

		baContent = soup.find("div", {"id": "ba-content"})
		#logging.debug("parse_breweries: ba-content: {}".format(baContent))
		table = baContent.find('table')
		#logging.debug("parse_breweries: table: {}".format(table))
		rows = table.find_all('a', href=re.compile('/beer/profile/'))
		#logging.debug("parse_breweries: rows: {}".format(rows))
		this_page_links = [r['href'] for r in rows]
		logging.debug("parse_breweries: this_page_links: {}".format(this_page_links))
		links.extend(this_page_links)

		next_page_tag = soup.find('a', text = "next")
		if next_page_tag:
			next_page_link = next_page_tag['href']
			parsed = urllib.parse.urlparse(next_page_link)
			next_page_start_str = urllib.parse.parse_qs(parsed.query)['start'][0]
			next_page_start = int(next_page_start_str)
		else:
			has_next = False
	
	logging.debug("parse_breweries: links: {}".format(links))
	return links


def parse_beers_from_breweries(links):
	logging.debug("parse_beers_from_brewery: brewery_links: {}".format(links))
	params = {'view': 'beers', 'show': 'all'}
	beer_links = []
	for link in links:
		brewery_url = urllib.parse.urljoin(domain, link)
		response = requests.get(url=brewery_url, params=params)
		soup = BeautifulSoup(response.text, features='lxml')
		baContent = soup.find("div", {"id":"ba-content"})
		#logging.debug("parse_beers_from_brewery: ba-content: {}".format(baContent))
	
		tables = baContent.find_all("table")
		if len(tables) < 3:
			logging.warning(link)
			continue
		beers_table = baContent.find_all("table")[2]
		#logging.debug("parse_beers_from_brewery: beers_table: {}".format(beers_table))

		sortable_table = soup.find("table", {"class": "sortable"})
		#logging.debug("parse_beers_from_brewery: sortable_table: {}".format(sortable_table))
		rows = sortable_table.tbody.find_all('a', href=re.compile('/beer/profile/'))
		#logging.debug("parse_beers_from_brewery: # rows: {}".format(len(rows)))

		this_brewery_links = [r['href'] for r in rows]
		logging.debug("parse_beers_from_brewery: this_brewery_links: {}".format(this_brewery_links))
		beer_links.extend(this_brewery_links)
	
	return beer_links


def parse_beer_details():
	for beer_url in beer_urls:
		url = BASE_URL + beer_url.select('@href').extract()[0]
		yield Request(url=url, callback=self.parse_beer_detail)


brewery_links = []


def get_last_page_start():
	response = requests.get(url=places_url, params=places_params)
	soup = BeautifulSoup(response.text, features='lxml')
	last_page_tag = soup.find('a', text="last")
	last_link = last_page_tag['href']
	parsed = urllib.parse.urlparse(last_link)
	last_start_str = urllib.parse.parse_qs(parsed.query)['start'][0]
	last_start = int(last_start_str)
	logging.debug("get_last_page_start: last_start: {}".format(last_start))
	return last_start


def get_brewery_links_async():
	reqs = []
	STEP = 20
	last_page_start = get_last_page_start()
	# HACK importing grequests at top of module causes requests to break
	import grequests
	for start in range(0, last_page_start, STEP):
		params = places_params.copy()
		params['start'] = start
		reqs.append(grequests.get(places_url, params=params, callback=get_brewery_links_handler))
	res = grequests.map(reqs, exception_handler=exception_handler)
	logging.debug("get_brewery_links_async: brewery_links: {}".format(brewery_links))


def get_brewery_links_handler(response, *args, **kwargs):
	print("HANDLER")
	soup = BeautifulSoup(response.text, features='lxml')
	baContent = soup.find("div", {"id": "ba-content"})
	#logging.debug("parse_breweries: ba-content: {}".format(baContent))
	table = baContent.find('table')
	#logging.debug("parse_breweries: table: {}".format(table))
	rows = table.find_all('a', href=re.compile('/beer/profile/'))
	#logging.debug("parse_breweries: rows: {}".format(rows))
	this_page_links = [r['href'] for r in rows]
	logging.info("parse_breweries: this_page_links: {}".format(this_page_links))
	brewery_links.extend(this_page_links)


def exception_handler(r, e):
	print(e)


beer_urls = []
breweries = []


def get_breweries_async():
	# HACK importing grequests at top of module causes requests to break
	import grequests
	params = {'view': 'beers', 'show': 'all'}
	reqs = []
	for url in brewery_links:
		urllib.parse.urljoin()
		reqs.append(grequests.get(places_url, params=params, callback=get_breweries_handler))
	res = grequests.map(reqs)


def get_breweries_handler(response, *args, **kwargs):
	soup = BeautifulSoup(response.text, features='lxml')
	this_brewery_beer_urls = parse_beers_from_brewery(soup)
	beer_urls.extend(this_brewery_beer_urls)
	brewrey_name = parse_brewery_details(soup)
	brewery_id = parse_brewery_id(url)
	brewery = {'id': brewery_id, 'name': brewery_name}
	breweries.append(brewery)


def parse_beers_from_brewery(soup):
	baContent = soup.find("div", id="baContent")
	beers_table = baContent.table()[2].tr()[1].td().table()
	beer_urls = beers_table.find_all('a', "/beer/profile/")
	return beer_urls


def parse_brewery_name(soup):
	title_bar = soup.find('div', {"class": "titleBar"})
	name = title_bar.h1.text
	return name


def parse_brewery_id(url):
	parsed = urllib.parse.urlparse(url)
	path = parsed.path
	brewery_id = os.path.split(path)[1]
	#split = urllib.parse.urlsplit(url)
	return brewery_id


def write_breweries():
	# Placeholder
	with open('breweries.json', 'w') as f:
		json.dump(breweries, f) 


def write_breweries_db():
	brewery_tuples = [b.items() for b in breweries]
	c.executemany("INSERT INTO breweries VALUES (?,?)", brewery_tuples)


beers = []


def get_beers_async():
	# HACK importing grequests at top of module causes requests to break
	import grequests
	reqs = []
	for beer_url in beer_urls:
		url = urllib.parse.urljoin(domain, beer_url)
		reqs.append(grequests.get(url, callback=get_breweries_handler))
	res = grequests.map(reqs)


def get_beers_handler(response, *args, **kwargs):
	soup = BeautifulSoup(response.text, features='lxml')
	beer = {}
	beer['id'] = parse_beer_id()
	beer['brewery_id'] = parse_brewery_id()
	beer['name'] = parse_beer_name()
	beer['score'] = parse_beer_score()
	beer['ratings'] = parse_beer_ratings()	
	beer['ranking'] = parse_beer_ranking()
	beer['style'] = parse_beer_style()
	beer['abv'] = parse_beer_abv()	
	beer['last'] = parse_beer_last_rating()
	beers.append(beer)


def parse_beer_id(url):
	parsed = urllib.parse.urlparse(url)
	path = parsed.path
	beer_id = os.path.split(path)[1]
	#split = urllib.parse.urlsplit(url)
	return beer_id


def parse_brewery_id_beer_profile(url):
	parsed = urllib.parse.urlparse(url)
	path = parsed.path
	brewery_id = os.path.split(path)[0].os.path.split(path)[1]
	#split = urllib.parse.urlsplit(url)
	return brewery_id


def parse_beer_name(soup):
	pass


def parse_beer_score(soup):
	pass


def parse_beer_ratings(soup):
	pass


def parse_beer_ranking(soup):
	pass


def parse_beer_style(soup):
	pass


def parse_beer_abv(soup):
	pass


def parse_beer_last_rating(soup):
	pass


def write_beers():
	with open('beers.json', 'w') as f:
		json.dump(beers, f)


def write_beers_db():
	beer_tuples = [b.items() for b in beers]
	c.executemany("INSERT INTO beers VALUES (?,?,?,?,?,?,?,?,?)", beer_tuples)


def main():
	brewery_links = parse_breweries()
	with open('breweries_single.json', 'w') as f:
		json.dump(brewery_links, f)
	beer_links = parse_beers_from_breweries(brewery_links)
	with open('beers_single.json', 'w') as f:
		json.dump(beer_links, f)


def main_async():
	get_brewery_links_async()
	get_breweries_async()
	write_breweries()
	get_beers_async()
	write_beers()
	

if __name__ == "__main__":
	if len(sys.argv) == 2:
		if sys.argv[1] == "async":
			print("async")
			main_async()
	elif len(sys.argv) == 3:
		if sys.argv[1] == "parse_beers":
			brewery_links_file = sys.argv[2]
			with open(brewery_links_file) as f:
				brewery_links = json.load(f)
			beer_links = parse_beers_from_breweries(brewery_links)
			with open('beers_single_2.json', 'w') as f:
				json.dump(beer_links, f)
	else:
		main()

