CREATE OR REPLACE VIEW UserActivitySummary AS
SELECT 
    u.user_id,
    u.name,
    COUNT(DISTINCT ul.media_id) AS total_likes,
    COUNT(DISTINCT ur.media_id) AS total_ratings,
    ROUND(AVG(ur.rating_value), 2) AS avg_rating
FROM Users u
LEFT JOIN UserLikes ul ON u.user_id = ul.user_id
LEFT JOIN UserRatings ur ON u.user_id = ur.user_id
GROUP BY u.user_id, u.name;