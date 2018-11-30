import os
import re
from bs4 import BeautifulSoup
import grequests
import requests
import urllib
import pprint


domain = 'https://www.beeradvocate.com/'
search_path = 'search/'

profile_url_re = re.compile(r'/beer/profile/[0-9]+/[0-9]+/?')
full_url_re = re.compile(r'https?://www\.beeradvocate\.com/')

redirects = {}
ratings = {}
to_fetch = []
no_results = []


def handler(response, *args, **kwargs):
	if response.status_code != 200:
		# Need to track redirects to determine which query originated response.
		# The name of the beer could be extracted from the final page but the
		# exact name may differ which will cause issues as the name is used as
		# a dictionary key.
		if not full_url_re.match(response.headers['Location']):
			location = urllib.parse.urljoin(domain, response.headers['Location'])
		else:
			location = response.headers['Location']
		redirects[location] = response.url
		return

	if not landed_on_profile(response):
		print("landed on search page: URL:", response.url)
		profile_urls = profile_url_re.findall(response.text)
		# TODO
		if profile_urls:
			# Naively choose profile from results
			profile_url = profile_urls[0]
			if not full_url_re.match(profile_url):
				location = urllib.parse.urljoin(domain, profile_url)
			else:
				location = profile_url
			redirects[location] = response.url
			req = grequests.get(urllib.parse.urljoin(domain, profile_url), callback=handler)
			to_fetch.append(grequests.send(req))
		else:
			og_url = reverse_redirects(response.url)
			parsed = urllib.parse.urlparse(og_url)
			q = urllib.parse.parse_qs(parsed.query)['q'][0]
			no_results.append(q)
	else:
		print("landed on profile: URL:", response.url)
		score = rating(response)
		og_url = reverse_redirects(response.url)
		parsed = urllib.parse.urlparse(og_url)
		q = urllib.parse.parse_qs(parsed.query)['q'][0]
		ratings[q] = score


def reverse_redirects(url):
	while url in redirects:
		url = redirects[url]
	return url


def exception_handler(r, e):
	print(e)


def async_search_beers(names: list):
	search_url = domain + search_path
	reqs = []
	for n in names:
		params = {'q': n, 'qt': 'beer'}
		reqs.append(grequests.get(domain + search_path, params=params, callback=handler))
	res = grequests.map(reqs, exception_handler=exception_handler)
	grequests.gevent.joinall(to_fetch)
	redirects.clear()
	print("NO MATCHES:", no_results)
	return ratings


def search_beers(query: str):
	"""
	Search BeerAdvocate for beers.

	Args:
		query

	Returns:
		List of URL's to profiles for beers relevant to query.

	Raises:

	"""
	search_url = os.path.join(domain, search_path)
	params = {'q': query, 'qt': 'beer'}
	response = requests.get(url=search_url, params=params)

	if not landed_on_profile(response):
		print("landed on search page: URL:", response.url)
		profile_urls = profile_url_re.findall(response.text)
		# TODO
		if profile_urls:
			response = requests.get(domain + profile_urls[0])
		else:
			return None
	else:
		print("landed on profile: URL:", response.url)
	return rating(response)


def landed_on_profile(response):
	matches = profile_url_re.findall(response.url)
	return matches != []


def rating(response):
	soup = BeautifulSoup(response.text, features="lxml")
	score = soup.find(attrs={"class": "BAscore_big"})
	return score.getText()
