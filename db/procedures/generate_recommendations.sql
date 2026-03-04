-- ====================================================================
-- PROCEDURE: generate_recommendations
-- Scores media the current user has NOT interacted with based on:
--   - Shared genres with the user's liked media  (+2.0 per match)
--   - Shared tags with the user's liked media    (+1.5 per match)
--   - The user's own avg rating for that genre   (+rating bonus)
--
-- Exclusions (per-user, strict):
--   - Media the user has already liked
--   - Media the user has already saved to any list
-- ====================================================================

CREATE OR REPLACE PROCEDURE generate_recommendations(p_user_id INT)
AS $$
DECLARE
    v_media_record RECORD;
BEGIN
    -- Clear stale recommendations for this user only
    DELETE FROM Recommendations WHERE user_id = p_user_id;

    FOR v_media_record IN
        SELECT
            m.media_id,
            COUNT(DISTINCT matched_genres.genre_id) * 2.0 +
            COUNT(DISTINCT matched_tags.tag_id)     * 1.5 +
            COALESCE(
                -- Personalised rating signal: this user's own avg rating
                -- for the genres on this media item (not community average)
                (
                    SELECT AVG(ur2.rating_value)
                    FROM UserRatings ur2
                    JOIN MediaGenre mg3 ON ur2.media_id = mg3.media_id
                    WHERE ur2.user_id = p_user_id
                      AND mg3.genre_id IN (
                          SELECT mg4.genre_id
                          FROM MediaGenre mg4
                          WHERE mg4.media_id = m.media_id
                      )
                ),
                3.0  -- neutral baseline when user has no ratings yet
            ) AS calculated_score

        FROM Media m

        -- Genre overlap: only genres this user has encountered via their likes
        LEFT JOIN MediaGenre mg ON m.media_id = mg.media_id
        LEFT JOIN (
            SELECT DISTINCT mg2.genre_id
            FROM UserLikes ul
            JOIN MediaGenre mg2 ON ul.media_id = mg2.media_id
            WHERE ul.user_id = p_user_id
        ) matched_genres ON mg.genre_id = matched_genres.genre_id

        -- Tag overlap: only tags from this user's liked media
        LEFT JOIN MediaTag mt ON m.media_id = mt.media_id
        LEFT JOIN (
            SELECT DISTINCT mt2.tag_id
            FROM UserLikes ul
            JOIN MediaTag mt2 ON ul.media_id = mt2.media_id
            WHERE ul.user_id = p_user_id
        ) matched_tags ON mt.tag_id = matched_tags.tag_id

        WHERE
            -- Exclude media this user has already liked
            m.media_id NOT IN (
                SELECT media_id FROM UserLikes WHERE user_id = p_user_id
            )
            -- Exclude media this user has already added to any list
            AND m.media_id NOT IN (
                SELECT media_id FROM ListItem WHERE user_id = p_user_id
            )

        GROUP BY m.media_id

        -- Only surface items with a real taste match for THIS user
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