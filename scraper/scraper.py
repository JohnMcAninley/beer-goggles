import gevent.monkey
gevent.monkey.patch_all()

import re
import sys
import json
import queue
import logging
import sqlite3
import requests
import grequests
import threading
import urllib.parse
from bs4 import BeautifulSoup


logger = logging.getLogger('scraper_async')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('scraper_async.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

DB_FILENAME = "scraper.db"

MAX_SESSIONS = 100

domain = 'https://www.beeradvocate.com/'
places_rel_url = 'place/list/'
places_url = urllib.parse.urljoin(domain, places_rel_url)
places_params = {'start': 0, 'brewery': 'Y', 'sort': 'name'}

brewery_links = []


def exception_handler(r, e):
	print(e)


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


beer_urls = []
beer_ids = queue.Queue()
breweries = queue.Queue()
fetching_breweries = True


def get_brewery_details():
	params = {'view': 'beers', 'show': 'all'}
	reqs = []
	for url in brewery_links:
		brewery_url = urllib.parse.urljoin(domain, url)
		reqs.append(grequests.get(brewery_url, params=params, callback=get_brewery_details_handler))
	res = grequests.map(reqs, size=MAX_SESSIONS)


def get_brewery_details_handler(response, *args, **kwargs):
	soup = BeautifulSoup(response.text, features='lxml')
	this_brewery_beer_urls = parse_beers_from_brewery(soup)
	beer_urls.extend(this_brewery_beer_urls)
	for b in beer_urls:
		beer = {}
		beer['id'] = parse_beer_id(b)
		beer['brewery_id'] = parse_brewery_id_beer_profile(b)
		beer_ids.put(beer)
	brewery = {}
	brewery['name'] = parse_brewery_name(soup)
	brewery['id'] = parse_brewery_id(response.url)
	breweries.put(brewery)
	#logger.info(brewery)


def parse_beers_from_brewery(soup):
	baContent = soup.find("div", {"id":"ba-content"})
	#logger.debug("parse_beers_from_brewery: ba-content: {}".format(baContent))
	
	tables = baContent.find_all("table")
	if len(tables) < 3:
		logger.warning(link)
		return []
	beers_table = baContent.find_all("table")[2]
	#logger.debug("parse_beers_from_brewery: beers_table: {}".format(beers_table))

	sortable_table = soup.find("table", {"class": "sortable"})
	#logger.debug("parse_beers_from_brewery: sortable_table: {}".format(sortable_table))
	rows = sortable_table.tbody.find_all('a', href=re.compile('/beer/profile/'))
	#logger.debug("parse_beers_from_brewery: # rows: {}".format(len(rows)))

	beer_urls = [r['href'] for r in rows]
	#logger.info("parse_beers_from_brewery: beer_urls: {}".format(beer_urls))
	return beer_urls


def parse_brewery_name(soup):
	title_bar = soup.find('div', {"class": "titleBar"})
	name = title_bar.h1.text
	#logger.debug("parse_brewery_name: name: {}".format(name))
	return name


def parse_brewery_id(url):
	#logger.debug("parse_brewery_id: url: {}".format(url))
	path = urllib.parse.urlparse(url).path
	#logger.debug("parse_brewery_id: path: {}".format(path))
	brewery_id = [p for p in path.split('/') if p is not ''][-1]
	#logger.debug("parse_brewery_id: id: {}".format(brewery_id))
	return brewery_id


def write_breweries():
	print("write_breweries")
	with open('breweries_async.json', 'w') as f:
		while fetching_breweries:
			b = breweries.get()	
			json.dump(b, f)


def write_breweries_db():
	conn = sqlite3.connect(DB_FILENAME)	
	c = conn.cursor()
	while fetching_breweries or not breweries.empty() or not beer_ids.empty():
		if not breweries.empty():
			b = breweries.get()
			# TODO This is a less efficient way to do this.	
			c.execute("UPDATE breweries SET name = ? WHERE id = ?", (b['name'], b['id']))
			c.execute("INSERT OR IGNORE INTO breweries (id, name) VALUES (?,?)", (b['id'], b['name']))
			conn.commit()
		if not beer_ids.empty():
			b = beer_ids.get()
			# TODO This is a less efficient way to do this.	
			c.execute("UPDATE beers SET brewery_id = ? WHERE id = ?", (b['brewery_id'], b['id']))
			c.execute("INSERT OR IGNORE INTO beers (id, brewery_id) VALUES (?, ?)", (b['id'], b['brewery_id']))
			conn.commit()
	conn.close()

"""
def write_beer_ids_db():
	conn = sqlite3.connect(DB_FILENAME)	
	c = conn.cursor()
	while fetching_breweries or not beer_ids.empty():
		b = beer_ids.get()
		# TODO This is a less efficient way to do this.	
		c.execute("UPDATE beers SET brewery_id = ? WHERE id = ?", (b['brewery_id'], b['id']))
		c.execute("INSERT OR IGNORE INTO beers (id, brewery_id) VALUES (?, ?)", (b['id'], b['brewery_id']))
		conn.commit()
	conn.close()
"""

beers = queue.Queue()
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
	beer['id'] = parse_beer_id()
	beer['brewery_id'] = parse_brewery_id_beer_profile()
	beer['name'] = parse_beer_name()
	beer['score'] = parse_beer_score()
	beer['ratings'] = parse_beer_ratings()	
	beer['ranking'] = parse_beer_ranking()
	beer['style'] = parse_beer_style()
	beer['abv'] = parse_beer_abv()	
	#beer['last'] = parse_beer_last_rating()
	beers.put(beer)


def parse_beer_id(url):
	#logger.debug("parse_beer_id: url: {}".format(url))
	path = urllib.parse.urlparse(url).path
	#logger.debug("parse_beer_id: path: {}".format(path))
	beer_id = [p for p in path.split('/') if p is not ''][-1]
	#logger.debug("parse_beer_id: id: {}".format(beer_id))
	return beer_id


def parse_brewery_id_beer_profile(url):
	#logger.debug("parse_brewery_id_beer_profile: url: {}".format(url))
	path = urllib.parse.urlparse(url).path
	#logger.debug("parse_brewery_id_beer_profile: path: {}".format(path))
	brewery_id = [p for p in path.split('/') if p is not ''][-2]
	#logger.debug("parse_brewery_id_beer_profile: id: {}".format(brewery_id))
	return brewery_id


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


def print_usage():
	print("USAGE: python3 scraper.py [beer_links filename]")


if __name__ == "__main__":
	if len(sys.argv) < 2:
		main()
	elif len(sys.argv) == 3 and sys.argv[1] == "beer_links":
		main_from_brewery_links(sys.argv[2]) 
	else:
		print_usage()

