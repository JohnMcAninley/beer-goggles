import re
from bs4 import BeautifulSoup

from . import url


def breweries(soup):

	baContent = soup.find("div", {"id": "ba-content"})
	table = baContent.find('table')
	links = table.find_all('a', href=re.compile('/beer/profile/'))
	this_page_breweries = [{'id': url.brewery_id(l['href']), 'name': l.text} for l in links]
	return this_page_breweries
