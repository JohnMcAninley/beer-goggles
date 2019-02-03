#!/usr/bin/python3

import sqlite3

import scraper


def add_new_breweries():
	scraper.get_breweries_async()
	brewery_tuples = [b.items() for b in scraper.breweries]
	c.executemany("INSERT OR IGNORE INTO breweries VALUES (?,?)", brewery_tuples)


def add_new_beers():
	scraper.get_beers_async()
	beer_tuples = [b.items() for b in scraper.beers]
	c.executemany("INSERT OR IGNORE INTO beers VALUES (?,?,?,?,?,?,?,?,?)", beer_tuples)


def update_beer_ratings():
	ratings_tuples = [(b['score'], b['ratings'], b['ranking'], b['last'], b['id']) for b in scraper.beers]
	c.executemany("UPDATE beers SET score = ?, ratings = ?, ranking = ?, last = ? WHERE id = ?", ratings_tuples)	


def main():
	add_new_breweries()
	add_new_beers()
	update_beer_ratings()


if __name__ == "__main__":
	main()
