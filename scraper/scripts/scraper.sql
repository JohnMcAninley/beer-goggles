CREATE TABLE breweries (
	id INT PRIMARY KEY UNIQUE NOT NULL,
	name TEXT
);

CREATE TABLE beers (
	id INT PRIMARY KEY UNIQUE NOT NULL,
	brewery_id INT,
	name TEXT,
	score REAL,
	ratings INT,
	ranking INT,
	style TEXT,
	abv REAL,
	last DATETIME
);
