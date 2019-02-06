import os
import logging
import sqlite3
import collections


logger = logging.getLogger('scraper')

SRC_DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(SRC_DIR, "..", "data")
DB_FILENAME = "scraper.db"
DB_FILEPATH = os.path.join(DATA_DIR, DB_FILENAME)

breweries = collections.deque()
beers = collections.deque()
fetching_breweries = True


def read_brewery_ids():
	conn = sqlite3.connect(DB_FILEPATH)	
	c = conn.cursor()
	#c.execute("SELECT id FROM breweries WHERE last_modified IS NULL")
	#c.execute("""SELECT id FROM breweries WHERE last_modified IS NULL AND 
	#	id NOT IN (SELECT DISTINCT brewery_id FROM beers WHERE brewery_id NOT NULL)""")
	c.execute("""SELECT id FROM breweries WHERE last_modified IS NULL AND 
		id NOT IN (SELECT DISTINCT brewery_id FROM beers WHERE brewery_id NOT NULL)""")
	vals_tuple = c.fetchall()
	ids = [(b[0]) for b in vals_tuple]
	return ids


def read_beer_ids():
	conn = sqlite3.connect(DB_FILEPATH)	
	c = conn.cursor()
	c.execute("SELECT brewery_id, id FROM beers;")
	ids = c.fetchall()
	return ids


def consumer():
	conn = sqlite3.connect(DB_FILEPATH)	
	c = conn.cursor()
	while fetching_breweries or len(breweries) or len(beers):
		write_breweries(conn, c)
		write_beers(conn, c)
	conn.close()


def write_breweries(conn, c):
	writable = len(breweries)
	if writable:
		to_write = [breweries.pop() for b in range(writable)]
		tuples_to_write = [(b['name'], b['id']) for b in to_write]
		# TODO This is a less efficient way to do this.	An UPSERT type SQL query
		# 		should perform better.
		c.executemany("UPDATE breweries SET name = ?, last_modified = datetime('now') WHERE id = ?",
			 tuples_to_write)
		c.executemany("""INSERT OR IGNORE INTO breweries (name, last_modified, id) 
			VALUES (?,datetime('now'),?)""", tuples_to_write)
		conn.commit()
		logger.info("WROTE {} breweries to DB.".format(len(to_write)))


def write_beers(conn, c):
	min_writable = len(beers)
	if min_writable:
		to_write = [beers.pop() for b in range(min_writable)]
		tuples_to_write = [(b['brewery_id'], b['name'], b['score'], 
			b['ratings'], b['style'], b['abv'], b['id']) for b in to_write]
		#TODO This is a less efficient way to do this. An UPSERT type SQL query
		# 		should perform better.
		c.executemany("""UPDATE beers SET brewery_id = ?, name = ?, score = ?,
			ratings = ?, style = ?, abv = ?, last = datetime('now') WHERE id = ?""", 
			tuples_to_write)
		c.executemany("""INSERT OR IGNORE INTO beers (brewery_id, name, score, 
			ratings, style, abv, id, last) VALUES (?,?,?,?,?,?,?, datetime('now'))""", 
			tuples_to_write)
		conn.commit()
		logger.info("WROTE {} beers to DB.".format(len(to_write)))


# Use the following methods once a unified query is established.


def batch_write_breweries(conn, c):
	query = """INSERT OR IGNORE INTO breweries (name, last_modified, id) 
			VALUES (?, datetime('now'), ?)"""
	cols = ["name", "id"]
	batch_write(conn, c, "breweries", cols, query, breweries)


def batch_write_beers(conn, c):
	query = """INSERT OR IGNORE INTO beers (brewery_id, name, score, 
			ratings, style, abv, id, last) VALUES (?,?,?,?,?,?,?, datetime('now'))"""
	cols = ["brewery_id", "brewery_id", "name", "score", 
			"ratings", "style", "abv", "id", "last"]
	batch_write(conn, c, "beers", cols, query, beers)


def batch_write(conn, c, table, cols, query, q):
	writable = len(q)
	if writable:
		to_write = [q.pop() for i in range(writable)]
		tuples = q2tuples(q, cols)
		c.executemany(query, tuples)
		conn.commit()


def q2tuples(q, cols):
	return [tuple(r[c] for c in cols) for r in q]
		
