CREATE OR REPLACE VIEW TopRatedMediaView AS
SELECT 
    m.media_id,
    m.title,
    ROUND(AVG(ur.rating_value), 2) AS avg_rating,
    COUNT(ur.rating_id) AS rating_count
FROM Media m
LEFT JOIN UserRatings ur ON m.media_id = ur.media_id
GROUP BY m.media_id, m.title
ORDER BY avg_rating DESC, rating_count DESC;