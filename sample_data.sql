INSERT INTO Users (name, email, password_hash, role)
VALUES 
('Alice', 'alice@test.com', 'hashed_pw', 'user'),
('Bob', 'bob@test.com', 'hashed_pw', 'admin'),
('Charlie', 'charlie@test.com', 'hashed_pw', 'user');

INSERT INTO MediaType (type_name)
VALUES ('movie'), ('book'), ('music')
ON CONFLICT DO NOTHING;

INSERT INTO Media (title, description, release_year, type_id)
VALUES
('The Matrix', 'Sci-fi movie', 1999, 1),
('Inception', 'Mind-bending movie', 2010, 1),
('1984', 'Dystopian novel', 1949, 2);

INSERT INTO Genre (genre_name)
VALUES ('Sci-Fi'), ('Action'), ('Dystopian');

INSERT INTO MediaGenre (media_id, genre_id)
VALUES
(1, 1),
(1, 2),
(2, 1),
(2, 2),
(3, 3);

INSERT INTO Tag (tag_name)
VALUES ('Classic'), ('Blockbuster'), ('Must Read');

INSERT INTO MediaTag (media_id, tag_id)
VALUES
(1, 1),
(1, 2),
(2, 2),
(3, 3);

INSERT INTO UserLikes (user_id, media_id)
VALUES
(1, 1),
(1, 2),
(2, 1),
(3, 3);

INSERT INTO UserRatings (user_id, media_id, rating_value)
VALUES
(1, 1, 5),
(1, 2, 4),
(2, 1, 4),
(3, 3, 5);

INSERT INTO ListItem (user_id, media_id, list_type)
VALUES
(1, 1, 'watchlist'),
(1, 2, 'playlist'),
(2, 1, 'readlist'),
(3, 3, 'watchlist');