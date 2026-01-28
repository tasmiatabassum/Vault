CREATE OR REPLACE FUNCTION func_generate_instant_recs()
RETURNS TRIGGER AS $$
BEGIN
    -- This inserts multiple rows into Recommendations based on shared genres
    INSERT INTO Recommendations (user_id, media_id, score)
    SELECT 
        NEW.user_id, 
        mg2.media_id, 
        0.75 -- Base score for genre match
    FROM MediaGenre mg1
    JOIN MediaGenre mg2 ON mg1.genre_id = mg2.genre_id
    WHERE mg1.media_id = NEW.media_id 
      AND mg2.media_id != NEW.media_id
    LIMIT 5
    ON CONFLICT DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_complex_recommendation
AFTER INSERT ON UserLikes
FOR EACH ROW
EXECUTE FUNCTION func_generate_instant_recs();