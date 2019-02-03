import sqlite3


db_name = ""
conn = sqlite3.connect(db_name)


def fetch():
	# if name is in db
	c = conn.cursor(()
	c.execute("SELECT * FROM beers WHERE NAME = ? COLLATE NOCASE", name)
	c.fetchone()
	# else
	# do normal fetch
	# update db



