#import gevent.monkey
#gevent.monkey.patch_all()
import os
import sys
import time
import pprint
import logging
import requests
import grequests
import threading
import urllib.parse
from bs4 import BeautifulSoup

import db
import parse


logger = logging.getLogger('scraper')
logger.setLevel(logging.DEBUG)

SRC_DIR = os.path.dirname(os.path.realpath(__file__))
LOG_DIR = os.path.join(SRC_DIR, "..", "log")
LOG_FILENAME = "scraper.log"
LOG_FILEPATH = os.path.join(LOG_DIR, LOG_FILENAME)
fh = logging.FileHandler(LOG_FILEPATH, mode='w')
fh.setLevel(logging.ERROR)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

# Set low so server isn't bombarded and begins to refuse.
MAX_SESSIONS = 1

domain = 'https://www.beeradvocate.com/'
places_rel_url = 'place/list/'
places_url = urllib.parse.urljoin(domain, places_rel_url)
places_params = {'start': 0, 'brewery': 'Y', 'sort': 'name'}

progress = {'breweries': 0, 'beers': 0, 'errors': 0}


def exception_handler(r, e):
	progress['errors'] += 1
	logger.error("REQUEST URL: {} EXCEPTION: {}".format(r.url, e))
	logger.error("{} ERRORS HAVE OCCURRED".format(progress['errors']))


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


def get_breweries():
	STEP = 20
	last_page_start = get_last_page_start()
	reqs = []
	for start in range(0, last_page_start, STEP):
		params = places_params.copy()
		params['start'] = start
		reqs.append(grequests.get(places_url, params=params, callback=get_breweries_handler))
	logger.info("STARTING THREADS to fetch brewery details.")
	res = grequests.map(reqs, size=MAX_SESSIONS, exception_handler=exception_handler)


def get_breweries_handler(response, *args, **kwargs):
	soup = BeautifulSoup(response.text, features='lxml')
	this_page_breweries = parse.places.breweries(soup)
	logger.info("this_page_breweries: {}".format(pprint.pformat(this_page_breweries)))
	logger.info("response time (s): {}".format(response.elapsed))
	db.breweries.extendleft(this_page_breweries)
	progress['breweries'] += len(this_page_breweries)
	logger.info("FETCHED: {} breweries.".format(progress['breweries']))


def get_brewery_details(paths):
	params = {'view': 'beers', 'show': 'all'}
	reqs = []
	for p in paths:
		url = urllib.parse.urljoin(domain, p)
		reqs.append(grequests.get(url, params=params, 
			callback=get_brewery_details_handler))
	logger.info("STARTING THREADS to fetch brewery details.")
	res = grequests.map(reqs, size=MAX_SESSIONS, exception_handler=exception_handler)


def get_brewery_details_handler(response, *args, **kwargs):
	logger.info("RESPONSE received from {}".format(response.url))
	soup = BeautifulSoup(response.text, features='lxml')
	#############################################################################
	# This is possibly redundant as all this information can be gathered in the
	# previous operation when the links are fetched from places list.
	brewery = {}
	brewery['id'] = parse.url.brewery_id(response.url)
	brewery['name'] = parse.brewery.name(soup)
	db.breweries.appendleft(brewery)
	logger.info("ADDED brewery {} to write queue.".format(pprint.pformat(brewery))) 
	#############################################################################
	this_brewery_beers = parse.brewery.beers(soup)
	db.beers.extendleft(this_brewery_beers)
	logger.info("ADDED {} beers to write queue.".format(len(this_brewery_beers)))
	progress['breweries'] += 1
	progress['beers'] += len(this_brewery_beers)
	logger.info("FETCHED: {} breweries and {} beers.".format(progress['breweries'], progress['beers']))
	time.sleep(1)


def get_beer_details(paths):
	# This function is redundant when first populating tha database as all info
	# can be extracted from the brewery profile page (except ranking which can be
	# calculated from scores stored in the database. It is useful to update the
	# info for beers already in the database but even when updating the previous
	# operation of fetching the brewery has most likely been performed anyway. 
	reqs = []
	for p in paths:
		url = urllib.parse.urljoin(domain, p)
		reqs.append(grequests.get(url, allow_redirects=True, callback=get_beer_details_handler))
	logger.info("STARTING THREADS to fetch beer details.")
	res = grequests.map(reqs, size=MAX_SESSIONS, exception_handler=exception_handler)


def get_beer_details_handler(response, *args, **kwargs):
	print(response.status_code)
	print(response.url)
	soup = BeautifulSoup(response.text, features='lxml')
	print(soup)
	beer = {}
	beer['id'] = parse.url.beer_id(response.url)
	beer['brewery_id'] = parse.url.brewery_id(response.url)
	beer['name'] = parse.beer.name(soup)
	logger.info("name: {}".format(beer['name']))
	beer['score'] = parse.beer.score(soup)
	logger.info("score: {}".format(beer['score']))
	beer['ratings'] = parse.beer.ratings(soup)	
	logger.info("ratings: {}".format(beer['ratings']))
	beer['ranking'] = parse.beer.ranking(soup)
	logger.info("ranking: {}".format(beer['ranking']))
	beer['style'] = parse.beer.style(soup)
	logger.info("style: {}".format(beer['style']))
	beer['abv'] = parse.beer.abv(soup)	
	logger.info("abv: {}".format(beer['abv']))
	db.beers.appendleft(beer)
	logger.info("ADDED beer with ID = {} to write queue.".format(beer['id']))


def breweries():
	consumer_thread = threading.Thread(target=db.consumer)
	consumer_thread.start()
	get_breweries()
	db.fetching_breweries = False
	consumer_thread.join()


def brewery_details():
	to_fetch = db.read_brewery_ids()
	logger.info("{} breweries to fetch".format(len(to_fetch)))
	paths = ["/beer/profile/{}/".format(b) for b in to_fetch]
	consumer_thread = threading.Thread(target=db.consumer)
	consumer_thread.start()
	get_brewery_details(paths)
	db.fetching_breweries = False
	consumer_thread.join()


def beer_details():
	to_fetch = db.read_beer_ids()
	logger.info("{} beers to fetch".format(len(to_fetch)))
	paths = ["/beer/profile/{}/{}".format(b[0], b[1]) for b in to_fetch]
	consumer_thread = threading.Thread(target=db.consumer)
	consumer_thread.start()
	get_beer_details(paths[0:1])
	db.fetching_breweries = False
	consumer_thread.join()


def print_usage():
	print("USAGE: python3 scraper.py {breweries|brewery_details|beer_details}")


if __name__ == "__main__":
	if len(sys.argv) < 2:
		print_usage()
	elif len(sys.argv) == 2 and sys.argv[1] == "brewery_details":
		brewery_details()
	elif len(sys.argv) == 2 and sys.argv[1] == "breweries":
		breweries()
	elif len(sys.argv) == 2 and sys.argv[1] == "beer_details":
		beer_details()
	else:
		print_usage()

