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
