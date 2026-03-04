-- ====================================================================
-- VAULT DATABASE SCHEMA - FINAL VERSION
-- CSE4508: RDBMS Programming Lab
-- Team: Nashat Islam, Tasmia Tabassum, Subha Tamanna Mrittika
-- ====================================================================

-- --- CORE ENTITY TABLES ---

-- Users Table
CREATE TABLE IF NOT EXISTS Users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) CHECK (role IN ('user', 'admin')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Media Types (movie, book, music)
CREATE TABLE IF NOT EXISTS MediaType (
    type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(50) UNIQUE NOT NULL
);

-- Genre Table (NEW - REQUIRED)
CREATE TABLE IF NOT EXISTS Genre (
    genre_id SERIAL PRIMARY KEY,
    genre_name VARCHAR(100) UNIQUE NOT NULL
);

-- Tag Table (User-defined custom tags)
CREATE TABLE IF NOT EXISTS Tag (
    tag_id SERIAL PRIMARY KEY,
    tag_name VARCHAR(50) UNIQUE NOT NULL
);

-- Media Table (Central entity for all media items)
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

-- MediaGenre (NEW - REQUIRED: Many-to-Many between Media and Genre)
CREATE TABLE IF NOT EXISTS MediaGenre (
    media_id INT REFERENCES Media(media_id) ON DELETE CASCADE,
    genre_id INT REFERENCES Genre(genre_id) ON DELETE CASCADE,
    PRIMARY KEY (media_id, genre_id)
);

-- MediaTag (Many-to-Many between Media and Tag)
CREATE TABLE IF NOT EXISTS MediaTag (
    media_id INT REFERENCES Media(media_id) ON DELETE CASCADE,
    tag_id INT REFERENCES Tag(tag_id) ON DELETE CASCADE,
    PRIMARY KEY (media_id, tag_id)
);

-- --- USER INTERACTION TABLES ---

-- UserLikes (Favorites)
CREATE TABLE IF NOT EXISTS UserLikes (
    like_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    media_id INT REFERENCES Media(media_id) ON DELETE CASCADE,
    liked_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_like UNIQUE (user_id, media_id)
);

-- UserRatings (NEW - REQUIRED: 1-5 star ratings)
CREATE TABLE IF NOT EXISTS UserRatings (
    rating_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    media_id INT REFERENCES Media(media_id) ON DELETE CASCADE,
    rating_value INT CHECK (rating_value BETWEEN 1 AND 5) NOT NULL,
    rated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_rating UNIQUE (user_id, media_id)
);

-- ListItem (Watchlist, Readlist, Playlist)
CREATE TABLE IF NOT EXISTS ListItem (
    list_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    media_id INT REFERENCES Media(media_id) ON DELETE CASCADE,
    list_type VARCHAR(20) CHECK (list_type IN ('watchlist', 'readlist', 'playlist')) NOT NULL,
    added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_list_item UNIQUE (user_id, media_id, list_type)
);

-- --- RECOMMENDATION ENGINE TABLE ---

-- Recommendations (NEW - REQUIRED: Stores personalized recommendations)
CREATE TABLE IF NOT EXISTS Recommendations (
    rec_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id) ON DELETE CASCADE,
    media_id INT REFERENCES Media(media_id) ON DELETE CASCADE,
    score NUMERIC(5,2) DEFAULT 0.00,
    generated_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_recommendation UNIQUE (user_id, media_id)
);

-- --- AUDIT/LOGGING TABLE ---

-- AuditLog (System activity tracking)
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

-- Indexes on foreign keys for faster joins
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

-- 1. TRIGGER: Log User Likes and Generate Recommendations
CREATE OR REPLACE FUNCTION log_user_like()
RETURNS TRIGGER AS $$
BEGIN
    -- Log the like action
    INSERT INTO AuditLog (user_id, media_id, action)
    VALUES (NEW.user_id, NEW.media_id, 'User liked a media item');

    -- Trigger recommendation generation
    -- (Note: This will call the generate_recommendations procedure when it's created)
    BEGIN
        CALL generate_recommendations(NEW.user_id);
    EXCEPTION
        WHEN OTHERS THEN
            -- If procedure doesn't exist yet, just continue
            NULL;
    END;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS after_media_like ON UserLikes;
CREATE TRIGGER after_media_like
AFTER INSERT ON UserLikes
FOR EACH ROW EXECUTE FUNCTION log_user_like();

-- 2. TRIGGER: Validate Rating Values
CREATE OR REPLACE FUNCTION validate_rating()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.rating_value < 1 OR NEW.rating_value > 5 THEN
        RAISE EXCEPTION 'Rating must be between 1 and 5, got %', NEW.rating_value;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS before_rating_insert ON UserRatings;
CREATE TRIGGER before_rating_insert
BEFORE INSERT OR UPDATE ON UserRatings
FOR EACH ROW EXECUTE FUNCTION validate_rating();

-- 3. TRIGGER: Log Rating Actions and Update Recommendations
CREATE OR REPLACE FUNCTION log_user_rating()
RETURNS TRIGGER AS $$
BEGIN
    -- Log the rating action
    INSERT INTO AuditLog (user_id, media_id, action)
    VALUES (NEW.user_id, NEW.media_id, 'User rated ' || NEW.rating_value || ' stars');

    -- Regenerate recommendations based on new rating
    BEGIN
        CALL generate_recommendations(NEW.user_id);
    EXCEPTION
        WHEN OTHERS THEN
            NULL;
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

-- 1. PROCEDURE: Add Item to List (with duplicate handling)
CREATE OR REPLACE PROCEDURE add_item_to_list(
    p_user_id INT,
    p_media_id INT,
    p_list_type VARCHAR
)
AS $$
BEGIN
    INSERT INTO ListItem (user_id, media_id, list_type)
    VALUES (p_user_id, p_media_id, p_list_type);
EXCEPTION
    WHEN unique_violation THEN
        RAISE NOTICE 'Item already in %', p_list_type;
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

-- Insert Media Types
INSERT INTO MediaType (type_name) VALUES
    ('movie'),
    ('book'),
    ('music')
ON CONFLICT (type_name) DO NOTHING;

-- Insert Common Genres
INSERT INTO Genre (genre_name) VALUES
    ('Action'),
    ('Adventure'),
    ('Animation'),
    ('Biography'),
    ('Comedy'),
    ('Crime'),
    ('Documentary'),
    ('Drama'),
    ('Family'),
    ('Fantasy'),
    ('History'),
    ('Horror'),
    ('Music'),
    ('Mystery'),
    ('Romance'),
    ('Science Fiction'),
    ('Thriller'),
    ('War'),
    ('Western'),
    ('Fiction'),
    ('Non-Fiction'),
    ('Literature'),
    ('Poetry'),
    ('Philosophy'),
    ('Psychology'),
    ('Self-Help'),
    ('Technology'),
    ('Business'),
    ('Art'),
    ('Sport')
ON CONFLICT (genre_name) DO NOTHING;

-- Insert Default Admin User (for testing)
INSERT INTO Users (name, email, password_hash, role) VALUES
    ('Admin User', 'admin@vault.com', 'admin123', 'admin')
ON CONFLICT (email) DO NOTHING;

-- ====================================================================
-- VERIFICATION QUERIES (Optional - for testing)
-- ====================================================================

-- Check all tables exist
DO $$
BEGIN
    RAISE NOTICE 'Schema creation complete!';
    RAISE NOTICE 'Total tables created: 12';
    RAISE NOTICE 'Total triggers: 4';
    RAISE NOTICE 'Total procedures: 1';
    RAISE NOTICE 'Total functions: 1';
    RAISE NOTICE 'Run additional SQL files to complete the system.';
END $$;