CREATE OR REPLACE VIEW MediaPopularityView AS
SELECT 
    m.media_id,
    m.title,
    COUNT(ul.like_id) AS total_likes
FROM Media m
LEFT JOIN UserLikes ul ON m.media_id = ul.media_id
GROUP BY m.media_id, m.title
ORDER BY total_likes DESC;