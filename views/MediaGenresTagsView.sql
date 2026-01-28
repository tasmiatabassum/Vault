CREATE OR REPLACE VIEW MediaGenresTagsView AS
WITH GenreCounts AS (
    SELECT media_id, COUNT(genre_id) as g_count 
    FROM MediaGenre GROUP BY media_id
),
TagCounts AS (
    SELECT media_id, COUNT(tag_id) as t_count 
    FROM MediaTag GROUP BY media_id
)
SELECT 
    m.media_id,
    m.title,
    STRING_AGG(DISTINCT g.genre_name, ' | ') AS genre_string,
    STRING_AGG(DISTINCT t.tag_name, ' | ') AS tag_string,
    COALESCE(gc.g_count, 0) as genre_count,
    COALESCE(tc.t_count, 0) as tag_count
FROM Media m
LEFT JOIN MediaGenre mg ON m.media_id = mg.media_id
LEFT JOIN Genre g ON mg.genre_id = g.genre_id
LEFT JOIN MediaTag mt ON m.media_id = mt.media_id
LEFT JOIN Tag t ON mt.tag_id = t.tag_id
LEFT JOIN GenreCounts gc ON m.media_id = gc.media_id
LEFT JOIN TagCounts tc ON m.media_id = tc.media_id
GROUP BY m.media_id, m.title, gc.g_count, tc.t_count;