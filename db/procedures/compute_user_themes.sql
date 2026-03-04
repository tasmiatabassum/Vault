CREATE OR REPLACE FUNCTION compute_user_theme_weights(p_user_id INT)
RETURNS TABLE(theme_name VARCHAR, weight NUMERIC, category VARCHAR)
AS $$
BEGIN
    RETURN QUERY
    -- Get genre preferences
    SELECT
        g.genre_name as theme_name,
        COUNT(*)::NUMERIC as weight,
        'Genre'::VARCHAR as category
    FROM UserLikes ul
    JOIN MediaGenre mg ON ul.media_id = mg.media_id
    JOIN Genre g ON mg.genre_id = g.genre_id
    WHERE ul.user_id = p_user_id
    GROUP BY g.genre_name

    UNION ALL

    -- Get tag preferences
    SELECT
        t.tag_name as theme_name,
        COUNT(*)::NUMERIC * 0.8 as weight,  -- Tags weighted slightly less
        'Tag'::VARCHAR as category
    FROM UserLikes ul
    JOIN MediaTag mt ON ul.media_id = mt.media_id
    JOIN Tag t ON mt.tag_id = t.tag_id
    WHERE ul.user_id = p_user_id
    GROUP BY t.tag_name

    ORDER BY weight DESC;
END;
$$ LANGUAGE plpgsql;