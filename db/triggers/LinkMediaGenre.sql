-- Trigger Function to link Genre
CREATE OR REPLACE FUNCTION link_media_to_genre()
RETURNS TRIGGER AS $$
DECLARE
    v_type_name VARCHAR;
BEGIN
    -- Get the type name (movie/book/music) to use as a fallback genre if needed
    SELECT type_name INTO v_type_name FROM MediaType WHERE type_id = NEW.type_id;
    
    -- Insert into MediaGenre (Logic assumes genre_name matches type_name for now)
    -- You can expand this to accept specific genre names from your API
    INSERT INTO MediaGenre (media_id, genre_id)
    SELECT NEW.media_id, g.genre_id 
    FROM Genre g WHERE g.genre_name = v_type_name
    ON CONFLICT DO NOTHING;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach Trigger
CREATE TRIGGER after_media_insert
AFTER INSERT ON Media
FOR EACH ROW EXECUTE FUNCTION link_media_to_genre();
-- 1. Enhanced Like Trigger (calls recommendations)
CREATE OR REPLACE FUNCTION log_user_like()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO AuditLog (user_id, media_id, action)
    VALUES (NEW.user_id, NEW.media_id, 'User liked a media item');

    -- Generate recommendations automatically
    CALL generate_recommendations(NEW.user_id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS after_media_like ON UserLikes;
CREATE TRIGGER after_media_like
AFTER INSERT ON UserLikes
FOR EACH ROW EXECUTE FUNCTION log_user_like();

-- 2. Rating Validation Trigger (NEW)
CREATE OR REPLACE FUNCTION validate_rating()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.rating_value < 1 OR NEW.rating_value > 5 THEN
        RAISE EXCEPTION 'Rating must be between 1 and 5, got %', NEW.rating_value;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER before_rating_insert
BEFORE INSERT ON UserRatings
FOR EACH ROW EXECUTE FUNCTION validate_rating();

-- 3. Rating Audit Trigger (NEW)
CREATE OR REPLACE FUNCTION log_user_rating()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO AuditLog (user_id, media_id, action)
    VALUES (NEW.user_id, NEW.media_id, 'User rated ' || NEW.rating_value || ' stars');

    -- Regenerate recommendations based on new rating
    CALL generate_recommendations(NEW.user_id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_rating_insert
AFTER INSERT OR UPDATE ON UserRatings
FOR EACH ROW EXECUTE FUNCTION log_user_rating();

-- 4. ListItem Audit Trigger (NEW)
CREATE OR REPLACE FUNCTION log_list_addition()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO AuditLog (user_id, media_id, action)
    VALUES (NEW.user_id, NEW.media_id, 'Added to ' || NEW.list_type);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_list_insert
AFTER INSERT ON ListItem
FOR EACH ROW EXECUTE FUNCTION log_list_addition();