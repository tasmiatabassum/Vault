CREATE OR REPLACE PROCEDURE submit_user_rating(
    p_user_id INT, 
    p_media_id INT, 
    p_rating INT
)
AS $$
BEGIN
    -- Insert or Update the rating (Upsert)
    INSERT INTO UserRatings (user_id, media_id, rating_value)
    VALUES (p_user_id, p_media_id, p_rating)
    ON CONFLICT (user_id, media_id) 
    DO UPDATE SET rating_value = EXCLUDED.rating_value;

    -- Log the rating action
    INSERT INTO AuditLog (user_id, media_id, action)
    VALUES (p_user_id, p_media_id, 'User submitted a ' || p_rating || '-star rating');
END;
$$ LANGUAGE plpgsql;
