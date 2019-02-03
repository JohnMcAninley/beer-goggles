import re
import sys
import json
import logging
import requests
import urllib.parse
from bs4 import BeautifulSoup


logger = logging.getLogger('scraper_single')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('scraper_single.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)


domain = 'https://www.beeradvocate.com/'
places_rel_url = 'place/list/'
places_url = urllib.parse.urljoin(domain, places_rel_url)
places_params = {'start': 0, 'brewery': 'Y', 'sort': 'name'}


def get_brewery_links():	
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


def get_beer_links_from_breweries(links):
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


def main():
	brewery_links = get_brewery_links()
	with open('brewery_links_single.json', 'w') as f:
		json.dump(brewery_links, f)
	beer_links = get_beer_links_from_breweries(brewery_links)
	with open('beer_links_single.json', 'w') as f:
		json.dump(beer_links, f)


def main_from_brewery_links(filename):
	with open(filename) as f:
		brewery_links = json.load(f)
	beer_links = get_beer_links_from_breweries(brewery_links)
	with open('beer_links_single.json', 'w') as f:
		json.dump(beer_links, f)


def print_usage():
	print("USAGE: python3 scraper_single.py [beer_links filename]")


if __name__ == "__main__":
	if len(sys.argv) < 2:
		main()
	elif len(sys.argv) == 3 and sys.argv[1] == "beer_links":
		main_from_brewery_links(sys.argv[2]) 
	else:
		print_usage()

