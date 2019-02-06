from bs4 import BeautifulSoup


def name(soup):
	mC = soup.find_all("div", {"class": "mainContent"})
	print("mainContent: {}".format(mC))
	title_bar = soup.find_all("div", {"class": "titleBar"})
	print("titleBar: {}".format(title_bar))
	name = title_bar.findChildren("h1")[0]
	return name.getText()


def score(soup):
	score = soup.find(attrs={"class": "BAscore_big"})
	return score.getText()


def ratings(soup):
	rating_count = soup.find("span", {"class": "ba-ratings"})
	return rating_count.getText()


def ranking(soup):
	item_stats = soup.find("div", {"id": "item_stats"})
	item_stats.find("dd", text=re.compile('#'))
	return rating_count.getText()


def style(soup):
	info_box = soup.find("div", {"id": "info_box"})
	bb = info_box.findChildren("b", text="Style:")[0]
	style = bb.find_next_sibling("a")
	return style


def abv(soup):
	info_box = soup.find("div", {"id": "info_box"})
	bb = info_box.findChildren("b", text="Alcohol by volume (ABV):")[0]
	abv = bb.find_next_sibling()
	return abv
