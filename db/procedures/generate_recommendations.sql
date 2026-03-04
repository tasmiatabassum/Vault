-- Main Recommendation Generation Procedure
CREATE OR REPLACE PROCEDURE generate_recommendations(p_user_id INT)
AS $$
DECLARE
    v_media_record RECORD;
    v_score NUMERIC;
BEGIN
    -- Clear old recommendations
    DELETE FROM Recommendations WHERE user_id = p_user_id;

    -- Generate new recommendations based on:
    -- 1. Genres of liked media
    -- 2. Tags on liked media
    -- 3. Similar ratings

    FOR v_media_record IN
        -- Find media that shares genres with user's likes
        SELECT DISTINCT m.media_id,
               COUNT(DISTINCT mg.genre_id) * 2.0 +  -- Genre matches worth 2 points
               COUNT(DISTINCT mt.tag_id) * 1.5 +     -- Tag matches worth 1.5 points
               COALESCE(AVG(ur.rating_value), 3.0) AS calculated_score
        FROM Media m
        -- Genre matching
        LEFT JOIN MediaGenre mg ON m.media_id = mg.media_id
        LEFT JOIN (
            SELECT DISTINCT mg2.genre_id
            FROM UserLikes ul
            JOIN MediaGenre mg2 ON ul.media_id = mg2.media_id
            WHERE ul.user_id = p_user_id
        ) user_genres ON mg.genre_id = user_genres.genre_id
        -- Tag matching
        LEFT JOIN MediaTag mt ON m.media_id = mt.media_id
        LEFT JOIN (
            SELECT DISTINCT mt2.tag_id
            FROM UserLikes ul
            JOIN MediaTag mt2 ON ul.media_id = mt2.media_id
            WHERE ul.user_id = p_user_id
        ) user_tags ON mt.tag_id = user_tags.tag_id
        -- Rating context
        LEFT JOIN UserRatings ur ON m.media_id = ur.media_id
        WHERE m.media_id NOT IN (
            -- Exclude already liked media
            SELECT media_id FROM UserLikes WHERE user_id = p_user_id
        )
        AND (user_genres.genre_id IS NOT NULL OR user_tags.tag_id IS NOT NULL)
        GROUP BY m.media_id
        HAVING COUNT(DISTINCT mg.genre_id) > 0 OR COUNT(DISTINCT mt.tag_id) > 0
        ORDER BY calculated_score DESC
        LIMIT 20
    LOOP
        INSERT INTO Recommendations (user_id, media_id, score)
        VALUES (p_user_id, v_media_record.media_id, v_media_record.calculated_score)
        ON CONFLICT (user_id, media_id) DO UPDATE
        SET score = EXCLUDED.score, generated_on = CURRENT_TIMESTAMP;
    END LOOP;

    -- Log the generation
    INSERT INTO AuditLog (user_id, action)
    VALUES (p_user_id, 'Generated recommendations');
END;
$$ LANGUAGE plpgsql;