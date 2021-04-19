CREATE TABLE anime_characters (
	id SERIAL PRIMARY KEY,
	anime_mal_id INTEGER NOT NULL,
	character_mal_id INTEGER NOT NULL,
	name_array TEXT[] NOT NULL,
	role VARCHAR(10),
	image_url TEXT
);


CREATE TABLE non_anime_characters (
	id SERIAL PRIMARY KEY,
	anime_mal_id INTEGER NOT NULL,
	name_array TEXT[] NOT NULL,
	role VARCHAR(10) DEFAULT 'Main',
	image_url TEXT
);