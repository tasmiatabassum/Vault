CREATE OR REPLACE VIEW MediaSearchGallery AS
SELECT 
    m.media_id,
    m.title,
    m.release_year,
    mt.type_name,
    COALESCE(STRING_AGG(g.genre_name, ', '), 'General') as genres
FROM Media m
JOIN MediaType mt ON m.type_id = mt.type_id
LEFT JOIN MediaGenre mg ON m.media_id = mg.media_id
LEFT JOIN Genre g ON mg.genre_id = g.genre_id
GROUP BY m.media_id, m.title, m.release_year, mt.type_name;
