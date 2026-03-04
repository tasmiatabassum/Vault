-- ====================================================================
-- PROCEDURE: generate_recommendations
-- Scores all media a user hasn't liked yet based on:
--   - Shared genres with liked media  (+2.0 per match)
--   - Shared tags with liked media    (+1.5 per match)
--   - Community average rating        (baseline weight)
-- Only media with at least one genre OR tag match is considered.
-- ====================================================================

CREATE OR REPLACE PROCEDURE generate_recommendations(p_user_id INT)
AS $$
DECLARE
    v_media_record RECORD;
BEGIN
    -- Clear stale recommendations for this user
    DELETE FROM Recommendations WHERE user_id = p_user_id;

    FOR v_media_record IN
        SELECT
            m.media_id,
            COUNT(DISTINCT matched_genres.genre_id) * 2.0 +
            COUNT(DISTINCT matched_tags.tag_id)     * 1.5 +
            COALESCE(AVG(ur.rating_value), 3.0)     AS calculated_score
        FROM Media m

        -- Genre matches: only genres the user has encountered via likes
        LEFT JOIN MediaGenre mg ON m.media_id = mg.media_id
        LEFT JOIN (
            SELECT DISTINCT mg2.genre_id
            FROM UserLikes ul
            JOIN MediaGenre mg2 ON ul.media_id = mg2.media_id
            WHERE ul.user_id = p_user_id
        ) matched_genres ON mg.genre_id = matched_genres.genre_id

        -- Tag matches: only tags from the user's liked media
        LEFT JOIN MediaTag mt ON m.media_id = mt.media_id
        LEFT JOIN (
            SELECT DISTINCT mt2.tag_id
            FROM UserLikes ul
            JOIN MediaTag mt2 ON ul.media_id = mt2.media_id
            WHERE ul.user_id = p_user_id
        ) matched_tags ON mt.tag_id = matched_tags.tag_id

        -- Community rating context
        LEFT JOIN UserRatings ur ON m.media_id = ur.media_id

        -- Exclude media the user already likes
        WHERE m.media_id NOT IN (
            SELECT media_id FROM UserLikes WHERE user_id = p_user_id
        )

        GROUP BY m.media_id

        -- Only keep media with at least one real genre or tag match
        HAVING
            COUNT(DISTINCT matched_genres.genre_id) > 0
            OR COUNT(DISTINCT matched_tags.tag_id) > 0

        ORDER BY calculated_score DESC
        LIMIT 20

    LOOP
        INSERT INTO Recommendations (user_id, media_id, score)
        VALUES (p_user_id, v_media_record.media_id, v_media_record.calculated_score)
        ON CONFLICT (user_id, media_id) DO UPDATE
            SET score        = EXCLUDED.score,
                generated_on = CURRENT_TIMESTAMP;
    END LOOP;

    INSERT INTO AuditLog (user_id, action)
    VALUES (p_user_id, 'Generated recommendations');
END;
$$ LANGUAGE plpgsql;