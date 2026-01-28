-- --- TABLES ---
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) CHECK (role in ('user', 'admin')) NOT NULL
);

CREATE TABLE MediaType (
    type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE Media ( 
    media_id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    release_year INT,
    type_id INT REFERENCES MediaType(type_id),
    CONSTRAINT unique_media_item UNIQUE (title, release_year) --
);

CREATE TABLE UserLikes (
    like_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id),
    media_id INT REFERENCES Media(media_id),
    liked_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, media_id)
);

CREATE TABLE AuditLog (
    log_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id),
    media_id INT REFERENCES Media(media_id),
    action VARCHAR(200),
    action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ListItem (
    list_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id),
    media_id INT REFERENCES Media(media_id),
    list_type VARCHAR(20) CHECK (list_type IN ('watchlist', 'readlist', 'playlist')),
    added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_list_item UNIQUE (user_id, media_id, list_type)
);

-- --- 1. TRIGGER (Nashat's Role) ---
-- Automatically logs a record whenever a user 'Likes' media
CREATE OR REPLACE FUNCTION log_user_like()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO AuditLog (user_id, media_id, action)
    VALUES (NEW.user_id, NEW.media_id, 'User liked a media item');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_media_like
AFTER INSERT ON UserLikes
FOR EACH ROW EXECUTE FUNCTION log_user_like();

-- --- 2. PROCEDURE (Nashat's Role) ---
-- Standardizes the workflow for adding items to lists with error handling
CREATE OR REPLACE PROCEDURE add_item_to_list(p_user_id INT, p_media_id INT, p_list_type VARCHAR)
AS $$
BEGIN
    INSERT INTO ListItem (user_id, media_id, list_type)
    VALUES (p_user_id, p_media_id, p_list_type);
EXCEPTION
    WHEN unique_violation THEN
        RAISE NOTICE 'Item already in %', p_list_type;
END;
$$ LANGUAGE plpgsql;

-- --- 3. FUNCTION (Tasmia/Nashat) ---
-- Calculates average ratings for the recommendation engine
CREATE OR REPLACE FUNCTION calculate_media_score(p_media_id INT)
RETURNS NUMERIC AS $$
BEGIN
    RETURN (SELECT COALESCE(AVG(rating_value), 0.00) FROM UserRatings WHERE media_id = p_media_id);
END;
$$ LANGUAGE plpgsql;

-- --- SEED DATA ---
INSERT INTO MediaType (type_name) VALUES ('movie'), ('book'), ('music') ON CONFLICT DO NOTHING;
