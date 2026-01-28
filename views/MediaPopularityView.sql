CREATE OR REPLACE VIEW MediaPopularityView AS
SELECT 
    m.media_id,
    m.title,
    mt.type_name,
    COUNT(ul.like_id) AS total_likes,
    -- Rank within its specific type (Movie vs Book)
    DENSE_RANK() OVER (PARTITION BY mt.type_id ORDER BY COUNT(ul.like_id) DESC) as rank_in_category,
    -- Percentile ranking across all media
    ROUND(CAST(PERCENT_RANK() OVER (ORDER BY COUNT(ul.like_id)) AS NUMERIC), 2) as popularity_percentile
FROM Media m
JOIN MediaType mt ON m.type_id = mt.type_id
LEFT JOIN UserLikes ul ON m.media_id = ul.media_id
GROUP BY m.media_id, m.title, mt.type_id, mt.type_name;

