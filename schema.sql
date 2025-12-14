CREATE TABLE Users ( --User is a reserved keyword in PostgreSQL; thus using Users
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) CHECK (role in ('user', 'admin')) NOT NULL
);



CREATE TABLE MediaType (
    type_id_id SERIAL PRIMARY KEY,
    type_name VARCHAR(50) NOT NULL
);

CREATE TABLE Media ( 
    media_id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    release_year INT,
    type_id INT REFERENCES MediaType(type_id)
);


CREATE TABLE Genre (
    genre_id SERIAL PRIMARY KEY,
    genre_name VARCHAR(100) NOT NULL
);

CREATE TABLE MediaGenre (
    media_id INT REFERENCES Media(media_id),
    genre_id INT REFERENCES Genre(genre_id),
    PRIMARY KEY (media_id, genre_id)
);

CREATE TABLE Tag (
    tag_id SERIAL PRIMARY KEY,
    tag_name VARCHAR(100) NOT NULL

);

CREATE TABLE MediaTag (
    media_id INT REFERENCES Media(media_id),
    tag_id INT REFERENCES Tag(tag_id),
    PRIMARY KEY (media_id, tag_id)
);

CREATE TABLE UserLikes (
    like_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id),
    media_id INT REFERENCES Media(media_id),
    liked_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE UserRatings (
    rating_id SERIALK PRIMARY KEY,
    user_id INT REFERENCES Users(user_id),
    media_id INT REFERENCES Media(media_id),
    rating_value INT CHECK (rating_value BETWEEN 1 AND 5),
    rated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ListItem (
    list_item_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id),
    media_id INT REFERENCES Media(media_id),
    list_type VARCHAR(20) CHECK (list_type IN ('watchlist', 'readlist', 'playlist')),
    added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);


CREATE TABLE Recommendations (
    rec_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id),
    media_id INT REFERENCES Media(media_id),
    score NUMERIC (5,2),
    generated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE AuditLog (
    log_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id),
    media_id INT REFERENCES Media(media_id),
    action VARCHAR(200),
    action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);