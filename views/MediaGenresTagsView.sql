CREATE OR REPLACE VIEW MediaGenresTagsView AS
SELECT 
    m.media_id,
    m.title,
    STRING_AGG(DISTINCT g.genre_name, ', ') AS genres,
    STRING_AGG(DISTINCT t.tag_name, ', ') AS tags
FROM Media m
LEFT JOIN MediaGenre mg ON m.media_id = mg.media_id
LEFT JOIN Genre g ON mg.genre_id = g.genre_id
LEFT JOIN MediaTag mt ON m.media_id = mt.media_id
LEFT JOIN Tag t ON mt.tag_id = t.tag_id
GROUP BY m.media_id, m.title
ORDER BY m.title;