CREATE OR REPLACE FUNCTION get_similar_media(p_media_id INT)
RETURNS TABLE(title VARCHAR, type_name VARCHAR, similarity_score BIGINT) 
AS $$
BEGIN
    RETURN QUERY
    SELECT m.title, mt.type_name, COUNT(*) as score
    FROM (
        -- 1. Find matches based on GENRE
        SELECT mg2.media_id
        FROM MediaGenre mg1
        JOIN MediaGenre mg2 ON mg1.genre_id = mg2.genre_id
        WHERE mg1.media_id = p_media_id 
          AND mg2.media_id != p_media_id
        
        UNION ALL
        
        -- 2. Find matches based on TAGS (The Fix)
        SELECT mt2.media_id
        FROM MediaTag mt1
        JOIN MediaTag mt2 ON mt1.tag_id = mt2.tag_id
        WHERE mt1.media_id = p_media_id 
          AND mt2.media_id != p_media_id
    ) matches
    JOIN Media m ON matches.media_id = m.media_id
    JOIN MediaType mt ON m.type_id = mt.type_id
    GROUP BY m.title, mt.type_name
    ORDER BY score DESC, m.title
    LIMIT 3;
END;
$$ LANGUAGE plpgsql;