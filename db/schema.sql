-- ====================================================================
-- VAULT DATABASE SCHEMA - FINAL MERGED VERSION
-- ====================================================================

-- --- CLEAR OLD DATA ---
DROP TABLE IF EXISTS Recommendations CASCADE;
DROP TABLE IF EXISTS MediaTag CASCADE;
DROP TABLE IF EXISTS Tag CASCADE;
DROP TABLE IF EXISTS AuditLog CASCADE;
DROP TABLE IF EXISTS ListItem CASCADE;
DROP TABLE IF EXISTS UserLikes CASCADE;
DROP TABLE IF EXISTS UserRatings CASCADE;
DROP TABLE IF EXISTS MediaGenre CASCADE;
DROP TABLE IF EXISTS Genre CASCADE;
DROP TABLE IF EXISTS Media CASCADE;
DROP TABLE IF EXISTS MediaType CASCADE;
DROP TABLE IF EXISTS Users CASCADE;

-- --- CORE ENTITY TABLES ---

CREATE TABLE IF NOT EXISTS Users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) CHECK (role IN ('user', 'admin')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS MediaType (
    type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS Genre (
    genre_id SERIAL PRIMARY KEY,
    genre_name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS Tag (
    tag_id SERIAL PRIMARY KEY,
    tag_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS Media (
    media_id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    release_year INT,
    type_id INT REFERENCES MediaType(type_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_media_item UNIQUE (title, release_year)
);

-- --- JUNCTION/RELATIONSHIP TABLES ---

CREATE TABLE IF NOT EXISTS MediaGenre (
    media_id INT REFERENCES Media(media_id) ON DELETE CASCADE,
    genre_id INT REFERENCES Genre(genre_id) ON DELETE CASCADE,
    PRIMARY KEY (media_id, genre_id)
);

CREATE TABLE IF NOT EXISTS MediaTag (
    media_id INT REFERENCES Media(media_id) ON DELETE CASCADE,
    tag_id INT REFERENCES Tag(tag_id) ON DELETE CASCADE,
    PRIMARY KEY (media_id, tag_id)
);

-- --- USER INTERACTION TABLES ---

CREATE TABLE IF NOT EXISTS UserLikes (
    like_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    media_id INT REFERENCES Media(media_id) ON DELETE CASCADE,
    liked_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_like UNIQUE (user_id, media_id)
);

CREATE TABLE IF NOT EXISTS UserRatings (
    rating_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    media_id INT REFERENCES Media(media_id) ON DELETE CASCADE,
    rating_value INT CHECK (rating_value BETWEEN 1 AND 5) NOT NULL,
    rated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_rating UNIQUE (user_id, media_id)
);

CREATE TABLE IF NOT EXISTS ListItem (
    list_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    media_id INT REFERENCES Media(media_id) ON DELETE CASCADE,
    list_type VARCHAR(20) CHECK (list_type IN ('watchlist', 'readlist', 'playlist')) NOT NULL,
    added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_list_item UNIQUE (user_id, media_id, list_type)
);

-- --- RECOMMENDATION ENGINE TABLE ---

CREATE TABLE IF NOT EXISTS Recommendations (
    rec_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    media_id INT REFERENCES Media(media_id) ON DELETE CASCADE,
    score NUMERIC(5,2) DEFAULT 0.00,
    generated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_recommendation UNIQUE (user_id, media_id)
);

-- --- AUDIT/LOGGING TABLE ---

CREATE TABLE IF NOT EXISTS AuditLog (
    log_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE SET NULL,
    media_id INT REFERENCES Media(media_id) ON DELETE SET NULL,
    action VARCHAR(200) NOT NULL,
    action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ====================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- ====================================================================

CREATE INDEX IF NOT EXISTS idx_media_type ON Media(type_id);
CREATE INDEX IF NOT EXISTS idx_user_likes_user ON UserLikes(user_id);
CREATE INDEX IF NOT EXISTS idx_user_likes_media ON UserLikes(media_id);
CREATE INDEX IF NOT EXISTS idx_user_ratings_user ON UserRatings(user_id);
CREATE INDEX IF NOT EXISTS idx_user_ratings_media ON UserRatings(media_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_user ON Recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_list_item_user ON ListItem(user_id);
CREATE INDEX IF NOT EXISTS idx_media_genre_media ON MediaGenre(media_id);
CREATE INDEX IF NOT EXISTS idx_media_genre_genre ON MediaGenre(genre_id);
CREATE INDEX IF NOT EXISTS idx_media_tag_media ON MediaTag(media_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON AuditLog(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_time ON AuditLog(action_time);

-- ====================================================================
-- TRIGGERS
-- ====================================================================

-- 1. TRIGGER: Validate Rating Year (Prevents rating unreleased media)
CREATE OR REPLACE FUNCTION validate_rating_year()
RETURNS TRIGGER AS $$
DECLARE
    v_release_year INT;
BEGIN
    SELECT release_year INTO v_release_year FROM Media WHERE media_id = NEW.media_id;
    IF v_release_year > EXTRACT(YEAR FROM CURRENT_DATE) THEN
        RAISE EXCEPTION 'Cannot rate a future release.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS before_rating_insert ON UserRatings;
CREATE TRIGGER before_rating_insert
BEFORE INSERT OR UPDATE ON UserRatings
FOR EACH ROW EXECUTE FUNCTION validate_rating_year();


-- 2. TRIGGER: Log User Likes and Generate Recommendations
CREATE OR REPLACE FUNCTION log_user_like()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO AuditLog (user_id, media_id, action)
    VALUES (NEW.user_id, NEW.media_id, 'User liked a media item');

    BEGIN
        CALL generate_recommendations(NEW.user_id);
    EXCEPTION WHEN OTHERS THEN NULL;
    END;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS after_media_like ON UserLikes;
CREATE TRIGGER after_media_like
AFTER INSERT ON UserLikes
FOR EACH ROW EXECUTE FUNCTION log_user_like();


-- 3. TRIGGER: Log Rating Actions and Update Recommendations
CREATE OR REPLACE FUNCTION log_user_rating()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO AuditLog (user_id, media_id, action)
    VALUES (NEW.user_id, NEW.media_id, 'User rated ' || NEW.rating_value || ' stars');

    BEGIN
        CALL generate_recommendations(NEW.user_id);
    EXCEPTION WHEN OTHERS THEN NULL;
    END;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS after_rating_insert ON UserRatings;
CREATE TRIGGER after_rating_insert
AFTER INSERT OR UPDATE ON UserRatings
FOR EACH ROW EXECUTE FUNCTION log_user_rating();


-- 4. TRIGGER: Log List Item Additions
CREATE OR REPLACE FUNCTION log_list_addition()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO AuditLog (user_id, media_id, action)
    VALUES (NEW.user_id, NEW.media_id, 'Added to ' || NEW.list_type);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS after_list_insert ON ListItem;
CREATE TRIGGER after_list_insert
AFTER INSERT ON ListItem
FOR EACH ROW EXECUTE FUNCTION log_list_addition();

-- ====================================================================
-- STORED PROCEDURES
-- ====================================================================

-- 1. PROCEDURE: Add Item to List (With Type Validation)
CREATE OR REPLACE PROCEDURE add_item_to_list(p_user_id INT, p_media_id INT, p_list_type VARCHAR)
AS $$
DECLARE
    v_type_name VARCHAR;
BEGIN
    SELECT mt.type_name INTO v_type_name 
    FROM Media m JOIN MediaType mt ON m.type_id = mt.type_id 
    WHERE m.media_id = p_media_id;

    IF (p_list_type = 'watchlist' AND v_type_name != 'movie') OR
       (p_list_type = 'readlist' AND v_type_name != 'book') OR
       (p_list_type = 'playlist' AND v_type_name != 'music') THEN
        RAISE EXCEPTION 'Type Mismatch: Only %s can be added to the %', v_type_name, p_list_type;
    END IF;

    -- Note: Audit logging is handled automatically by the after_list_insert trigger
    INSERT INTO ListItem (user_id, media_id, list_type) VALUES (p_user_id, p_media_id, p_list_type);
EXCEPTION
    WHEN unique_violation THEN
        RAISE NOTICE 'Item already in %', p_list_type;
END;
$$ LANGUAGE plpgsql;

-- 2. PROCEDURE: Submit User Rating (With Upsert Logic)
CREATE OR REPLACE PROCEDURE submit_user_rating(p_user_id INT, p_media_id INT, p_rating INT)
AS $$
BEGIN
    -- Note: Audit logging is handled automatically by the after_rating_insert trigger
    INSERT INTO UserRatings (user_id, media_id, rating_value)
    VALUES (p_user_id, p_media_id, p_rating)
    ON CONFLICT (user_id, media_id) 
    DO UPDATE SET rating_value = EXCLUDED.rating_value;
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- STORED FUNCTIONS
-- ====================================================================

-- 1. FUNCTION: Calculate Media Score (average rating)
CREATE OR REPLACE FUNCTION calculate_media_score(p_media_id INT)
RETURNS NUMERIC AS $$
BEGIN
    RETURN (
        SELECT COALESCE(AVG(rating_value), 0.00)
        FROM UserRatings
        WHERE media_id = p_media_id
    );
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- SEED DATA
-- ====================================================================

INSERT INTO MediaType (type_name) VALUES
    ('movie'),
    ('book'),
    ('music')
ON CONFLICT (type_name) DO NOTHING;

INSERT INTO Genre (genre_name) VALUES
    ('Action'), ('Adventure'), ('Animation'), ('Biography'),
    ('Comedy'), ('Crime'), ('Documentary'), ('Drama'),
    ('Family'), ('Fantasy'), ('History'), ('Horror'),
    ('Music'), ('Mystery'), ('Romance'), ('Science Fiction'),
    ('Thriller'), ('War'), ('Western'), ('Fiction'),
    ('Non-Fiction'), ('Literature'), ('Poetry'), ('Philosophy'),
    ('Psychology'), ('Self-Help'), ('Technology'), ('Business'),
    ('Art'), ('Sport')
ON CONFLICT (genre_name) DO NOTHING;

INSERT INTO Users (name, email, password_hash, role) VALUES
    ('Admin User', 'admin@vault.com', 'admin123', 'admin')
ON CONFLICT (email) DO NOTHING;

-- ====================================================================
-- VERIFICATION
-- ====================================================================
DO $$
BEGIN
    RAISE NOTICE 'Merged Schema creation complete!';
END $$;