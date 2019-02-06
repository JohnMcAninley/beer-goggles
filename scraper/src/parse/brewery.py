import re
import urllib.parse
from bs4 import BeautifulSoup

from . import url


def name(soup):
	title_bar = soup.find('div', {"class": "titleBar"})
	name = title_bar.h1.text
	#logger.debug("parse_brewery_name: name: {}".format(name))
	return name


def beers(soup):
	baContent = soup.find("div", {"id":"ba-content"})
	#logger.debug("parse_beers_from_brewery: ba-content: {}".format(baContent))
	
	sortable_table = soup.find("table", {"class": "sortable"})
	if not sortable_table:
		return []
	t_body = sortable_table.tbody

	this_brewery_beers = []

	for row in t_body:
		cols = row.find_all('td')
		beer = {}

		# Get Link and Name from 1st col
		#a = cols[0].find('a', href=re.compile('/beer/profile/'))
		a = cols[0].a
		link = a['href']
		beer['id'] = url.beer_id(link)
		# NOTE The brewery ID is extracted from the link to every beer because
		#				some places list beers that redirect to different breweries.
		beer['brewery_id'] = url.brewery_id(link)
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
