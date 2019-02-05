#import gevent.monkey
#gevent.monkey.patch_all()
import re
import sys
import json
import queue
import pprint
import logging
import sqlite3
import requests
import grequests
import threading
import collections
import urllib.parse
from bs4 import BeautifulSoup


logger = logging.getLogger('scraper_async')
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('scraper_async.log')
fh.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

DB_FILENAME = "scraper.db"

# Set low so server isn't bombarded and begins to refuse.
MAX_SESSIONS = 2

domain = 'https://www.beeradvocate.com/'
places_rel_url = 'place/list/'
places_url = urllib.parse.urljoin(domain, places_rel_url)
places_params = {'start': 0, 'brewery': 'Y', 'sort': 'name'}

brewery_links = []


def exception_handler(r, e):
	logger.error("REQUEST: {} EXCEPTION: {}".format(r, e))


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


def get_brewery_links():
	reqs = []
	STEP = 20
	last_page_start = get_last_page_start()
	for start in range(0, last_page_start, STEP):
		params = places_params.copy()
		params['start'] = start
		reqs.append(grequests.get(places_url, params=params, callback=get_brewery_links_handler))
	res = grequests.map(reqs, exception_handler=exception_handler)
	logging.debug("get_brewery_links_async: brewery_links: {}".format(brewery_links))


def get_brewery_links_handler(response, *args, **kwargs):
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


#beer_ids = queue.Queue()
#breweries = queue.Queue()
beers = collections.deque()
breweries = collections.deque()
fetching_breweries = True


def get_brewery_details():
	params = {'view': 'beers', 'show': 'all'}
	reqs = []
	for url in brewery_links:
		brewery_url = urllib.parse.urljoin(domain, url)
		reqs.append(grequests.get(brewery_url, params=params, 
			callback=get_brewery_details_handler))
	logger.info("STARTING THREADS to fetch brewery details.")
	res = grequests.map(reqs, size=MAX_SESSIONS, exception_handler=exception_handler)


def get_brewery_details_handler(response, *args, **kwargs):
	logger.info("RESPONSE received from {}".format(response.url))
	soup = BeautifulSoup(response.text, features='lxml')

	brewery = {}
	brewery['id'] = extract_brewery_id(response.url)
	brewery['name'] = parse_brewery_name(soup)
	breweries.appendleft(brewery)

	logger.info("ADDED brewery {} to write queue.".format(pprint.pformat(brewery))) 

	this_brewery_beers = parse_beers_from_brewery(soup)

	for b in this_brewery_beers:
		b['brewery_id'] = brewery['id']
	beers.extendleft(this_brewery_beers)

	logger.info("ADDED {} beers to write queue.".format(len(this_brewery_beers)))


def parse_beers_from_brewery(soup):
	baContent = soup.find("div", {"id":"ba-content"})
	#logger.debug("parse_beers_from_brewery: ba-content: {}".format(baContent))
	
	sortable_table = soup.find("table", {"class": "sortable"})
	t_body = sortable_table.tbody

	this_brewery_beers = []

	for row in t_body:
		cols = row.find_all('td')
		beer = {}

		# Get Link and Name from 1st col
		#a = cols[0].find('a', href=re.compile('/beer/profile/'))
		a = cols[0].a
		link = a['href']
		beer['id'] = extract_beer_id(link)
		# NOTE The brewery ID is extracted from the link to every beer because
		#				some places list beers that redirect to different breweries.
		beer['brewery_id'] = extract_brewery_id(link)
		beer['name'] = a.text

		# Get Style from 2nd col
		beer['style'] = a = cols[1].a.text

		# Get ABV from 3rd col
		abv_text = cols[2].text
		try:
			beer['abv'] = float(abv_text)
		except:
			beer['abv'] = None

		# Get Ratings from 4th col
		ratings_text = cols[3].text
		try:
			beer['ratings'] = float(ratings_text)
		except:
			beer['ratings'] = None

		# Get Score from 5th col
		score_text = cols[4].text
		try:
			beer['score'] = float(score_text)
		except:
			beer['score'] = None

		this_brewery_beers.append(beer)	

	return this_brewery_beers


def parse_brewery_name(soup):
	title_bar = soup.find('div', {"class": "titleBar"})
	name = title_bar.h1.text
	#logger.debug("parse_brewery_name: name: {}".format(name))
	return name


def extract_brewery_id(url):
	"""
	Extract the brewery's ID from the URL for a brewery profile in the form
	"/beer/profile/[brewery_id]" or from the URL for a beer in the form 
	"/beer/profile/[brewery_id]/[beer_id]".

	Raises:
		Error if the URL is not one of the above forms.
	"""
	path = urllib.parse.urlparse(url).path
	path_parts = [p for p in path.split('/') if p is not '']
	if len(path_parts) < 3:
		raise ValueError("Incorrect URL format.")
	if path_parts[0] != "beer" or path_parts[1] != "profile":
		raise ValueError("Incorrect URL format.")
	brewery_id = path_parts[2]
	return brewery_id


def extract_beer_id(url):
	"""
	Extract the beer ID from the URL for a beer profile in the form 
	"/beer/profile/[brewery_id]/[beer_id]".

	Raises:
		Error if the URL is not the above forms.
	"""
	path = urllib.parse.urlparse(url).path
	path_parts = [p for p in path.split('/') if p is not '']
	if len(path_parts) < 4:
		raise ValueError("Incorrect URL format.")
	if path_parts[0] != "beer" or path_parts[1] != "profile":
		raise ValueError("Incorrect URL format.")
	beer_id = path_parts[3]
	return beer_id


def write_breweries_db():
	# TODO Use deques instead of queues so writes can be batch processed.
	conn = sqlite3.connect(DB_FILENAME)	
	c = conn.cursor()
	while fetching_breweries or len(breweries) or len(beers):
		min_writable_brews = len(breweries)
		if min_writable_brews:
			#HACK Kinda hacky way to batch write without blocking. Another possibility
			#			is to acquire lock, copy and clear deque, then release lock.
			brews_to_write = [breweries.pop() for b in range(min_writable_brews)]
			brew_tuples_to_write = [(b['name'], b['id']) for b in brews_to_write]
			# TODO This is a less efficient way to do this.	An UPSERT type SQL query
			# 		should perform better.
			c.executemany("UPDATE breweries SET name = ?, last_modified = datetime('now') WHERE id = ?",
				 brew_tuples_to_write)
			c.executemany("""INSERT OR IGNORE INTO breweries (name, last_modified, id) 
				VALUES (?,datetime('now'),?)""", brew_tuples_to_write)
			conn.commit()
			logger.debug("WROTE {} breweries to DB.".format(len(brews_to_write)))
		min_writable_beers = len(beers)
		if min_writable_beers:
			#HACK Kinda hacky way to batch write without blocking. Another possibility
			#			is to acquire lock, copy and clear deque, then release lock.
			beers_to_write = [beers.pop() for b in range(min_writable_beers)]
			beer_tuples_to_write = [(b['brewery_id'], b['name'], b['score'], 
				b['ratings'], b['style'], b['abv'], b['id']) for b in beers_to_write]
			#TODO This is a less efficient way to do this. An UPSERT type SQL query
			# 		should perform better.
			c.executemany("""UPDATE beers SET brewery_id = ?, name = ?, score = ?,
				ratings = ?, style = ?, abv = ?, last = datetime('now') WHERE id = ?""", 
				beer_tuples_to_write)
			c.executemany("""INSERT OR IGNORE INTO beers (brewery_id, name, score, 
				ratings, style, abv, id, last) VALUES (?,?,?,?,?,?,?, datetime('now'))""", 
				beer_tuples_to_write)
			conn.commit()
			logger.debug("WROTE {} beers to DB.".format(len(beers_to_write)))
	conn.close()


fetching_beers = True


def get_beer_details():
	reqs = []
	for beer_url in beer_urls:
		url = urllib.parse.urljoin(domain, beer_url)
		reqs.append(grequests.get(url, callback=get_beer_details_handler))
	res = grequests.map(reqs, size=MAX_SESSIONS)


def get_beer_details_handler(response, *args, **kwargs):
	soup = BeautifulSoup(response.text, features='lxml')
	beer = {}
	beer['id'] = extract_beer_id()
	beer['brewery_id'] = extract_brewery_id()
	beer['name'] = parse_beer_name()
	beer['score'] = parse_beer_score()
	beer['ratings'] = parse_beer_ratings()	
	beer['ranking'] = parse_beer_ranking()
	beer['style'] = parse_beer_style()
	beer['abv'] = parse_beer_abv()	
	#beer['last'] = parse_beer_last_rating()
	beers.put(beer)


def parse_beer_name(soup):
	title_bar = soup.find("div", attrs={"class": "titleBar"})
	name = title_bar.findChildren("h1")[0]
	return name.getText()


def parse_beer_score(soup):
	score = soup.find(attrs={"class": "BAscore_big"})
	return score.getText()


def parse_beer_ratings(soup):
	rating_count = soup.find("span", attrs={"class": "ba-ratings"})
	return rating_count.getText()


def parse_beer_ranking(soup):
	item_stats = soup.find("div", {"id": "item_stats"})
	item_stats.find("dd", text=re.compile('#'))
	return rating_count.getText()


def parse_beer_style(soup):
	info_box = soup.find("div", attrs={"id": "info_box"})
	bb = info_box.findChildren("b", text="Style:")[0]
	style = bb.find_next_sibling("a")
	return style


def parse_beer_abv(soup):
	info_box = soup.find("div", attrs={"id": "info_box"})
	bb = info_box.findChildren("b", text="Alcohol by volume (ABV):")[0]
	abv = bb.find_next_sibling()
	return abv


def parse_beer_last_rating(soup):
	pass


def parse_brewery(response):
	soup = BeautifulSoup(response.text, features="lxml")
	info_box = soup.find("div", attrs={"id": "info_box"})
	bb = info_box.findChildren("b", text="Brewed by:")[0]
	brewery = bb.find_next_sibling("a")
	return brewery


def write_beers_db():
	conn = sqlite3.connect(DB_FILENAME)	
	c = conn.cursor()
	while fetching_beers or not beers.empty():
		b = beers.get()
		# TODO This is a less efficient way to do this.	
		c.execute("""UPDATE beers SET brewery_id = ?, name = ?, score = ?, 
			ratings = ?, ranking = ?, style = ?, abv = ? WHERE id = ?""",
			(b['brewery_id'], b['name'], b['score'], b['rating'],
				b['ranking'], b['style'], b['abv'], b['id']))
		c.execute("""INSERT OR IGNORE INTO beers (id, brewery_id, name, score, 
			ratings, ranking, style, abv) VALUES (?,?,?,?,?,?,?,?)""",
		(b['id'], b['brewery_id'], b['name'], b['score'], b['rating'],
				b['ranking'], b['style'], b['abv']))
		conn.commit()
	conn.close()



def main():
	get_brewery_links()
	get_brewery_details()
	write_breweries()
	get_beer_details()
	write_beers()


def main_from_brewery_links(filename):
	global brewery_links
	with open(filename) as f:
		brewery_links = json.load(f)
	write_brews_thread = threading.Thread(target=write_breweries_db)	
	#write_beers_thread = threading.Thread(target=write_beer_ids_db)	
	write_brews_thread.start()
	#write_beers_thread.start()
	get_brewery_details()
	global fetching_breweries
	fetching_breweries = False
	write_brews_thread.join()
	#write_beers_thread.join()


def brewery_details_from_brewery_links_db():
	logger.info("FETCHING BREWERY DETAILS FOR IDS IN DB.")
	conn = sqlite3.connect(DB_FILENAME)	
	c = conn.cursor()
	#c.execute("SELECT id FROM breweries WHERE last_modified IS NULL")
	#c.execute("""SELECT id FROM breweries WHERE last_modified IS NULL AND 
	#	id NOT IN (SELECT DISTINCT brewery_id FROM beers WHERE brewery_id NOT NULL)""")
	c.execute("""SELECT id FROM breweries WHERE last_modified IS NULL AND 
		id NOT IN (SELECT DISTINCT brewery_id FROM beers WHERE brewery_id NOT NULL)
		LIMIT 64""")
	breweries_to_fetch = c.fetchall()
	logger.info("{} breweries to fetch".format(len(breweries_to_fetch)))
	global brewery_links
	brewery_links = ["/beer/profile/{}/".format(b[0]) for b in breweries_to_fetch]
	write_brews_thread = threading.Thread(target=write_breweries_db)	
	write_brews_thread.start()
	get_brewery_details()
	global fetching_breweries
	fetching_breweries = False
	write_brews_thread.join()


def print_usage():
	print("USAGE: python3 scraper.py [beer_links filename]")


if __name__ == "__main__":
	if len(sys.argv) < 2:
		main()
	elif len(sys.argv) == 2 and sys.argv[1] == "db":
		brewery_details_from_brewery_links_db()
	elif len(sys.argv) == 3 and sys.argv[1] == "beer_links":
		main_from_brewery_links(sys.argv[2]) 
	else:
		print_usage()

