CREATE OR REPLACE VIEW TopRatedMediaView AS
SELECT 
    m.media_id,
    m.title,
    mt.type_name,
    ROUND(AVG(ur.rating_value), 2) AS avg_rating,
    COUNT(ur.rating_id) AS rating_count,
    -- Analytical Window Function: Average rating for all items of this specific type
    ROUND(AVG(AVG(ur.rating_value)) OVER(PARTITION BY mt.type_id), 2) as category_avg,
    -- Rank media by rating within its own type
    RANK() OVER(PARTITION BY mt.type_id ORDER BY AVG(ur.rating_value) DESC) as rank_in_type
FROM Media m
JOIN MediaType mt ON m.type_id = mt.type_id
LEFT JOIN UserRatings ur ON m.media_id = ur.media_id
GROUP BY m.media_id, m.title, mt.type_id, mt.type_name
HAVING COUNT(ur.rating_id) > 0;