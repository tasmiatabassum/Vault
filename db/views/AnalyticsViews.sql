-- 1. Top Rated Genres View
-- Uses Joins & Aggregation to find user preferences
CREATE OR REPLACE VIEW TopRatedGenresView AS
SELECT g.genre_name, ROUND(AVG(ur.rating_value), 2) as avg_rating, COUNT(ur.rating_id) as vote_count
FROM Genre g
JOIN MediaGenre mg ON g.genre_id = mg.genre_id
JOIN UserRatings ur ON mg.media_id = ur.media_id
GROUP BY g.genre_name
HAVING COUNT(ur.rating_id) > 0
ORDER BY avg_rating DESC;

-- 2. User Activity Level View
-- Uses CASE statements to categorize user behavior
CREATE OR REPLACE VIEW UserActivityView AS
SELECT u.name, 
       (COUNT(DISTINCT ul.like_id) + COUNT(DISTINCT ur.rating_id)) as total_actions,
       CASE 
           WHEN (COUNT(DISTINCT ul.like_id) + COUNT(DISTINCT ur.rating_id)) > 10 THEN 'Power User'
           WHEN (COUNT(DISTINCT ul.like_id) + COUNT(DISTINCT ur.rating_id)) > 2 THEN 'Active'
           ELSE 'Observer'
       END as status
FROM Users u
LEFT JOIN UserLikes ul ON u.user_id = ul.user_id
LEFT JOIN UserRatings ur ON u.user_id = ur.user_id
GROUP BY u.user_id, u.name
ORDER BY total_actions DESC;

-- 3. Format Popularity View
-- Simple Grouping to compare Movies vs Books vs Music
CREATE OR REPLACE VIEW FormatPopularityView AS
SELECT mt.type_name, COUNT(ul.like_id) as likes
FROM MediaType mt
JOIN Media m ON mt.type_id = m.type_id
LEFT JOIN UserLikes ul ON m.media_id = ul.media_id
GROUP BY mt.type_name
ORDER BY likes DESC;

-- 4. Hidden Gems View
-- Uses HAVING clause to filter high-rated but potentially low-visibility items
CREATE OR REPLACE VIEW HiddenGemsView AS
SELECT m.title, ROUND(AVG(ur.rating_value), 2) as score
FROM Media m
JOIN UserRatings ur ON m.media_id = ur.media_id
GROUP BY m.media_id, m.title
HAVING AVG(ur.rating_value) >= 4.0;

-- 5. System Health View
-- Time-based aggregation from the AuditLog
CREATE OR REPLACE VIEW SystemHealthView AS
SELECT action, COUNT(*) as freq 
FROM AuditLog 
GROUP BY action 
ORDER BY freq DESC;

-- 6. Top Rated Genres View
-- Uses Joins & Aggregation to find user preferences
CREATE OR REPLACE VIEW TopRatedGenresView AS
SELECT g.genre_name, ROUND(AVG(ur.rating_value), 2) as avg_rating, COUNT(ur.rating_id) as vote_count
FROM Genre g
JOIN MediaGenre mg ON g.genre_id = mg.genre_id
JOIN UserRatings ur ON mg.media_id = ur.media_id
GROUP BY g.genre_name
HAVING COUNT(ur.rating_id) > 0
ORDER BY avg_rating DESC;

-- 7. User Activity Level View
-- Uses CASE statements to categorize user behavior
CREATE OR REPLACE VIEW UserActivityView AS
SELECT u.name,
       (COUNT(DISTINCT ul.like_id) + COUNT(DISTINCT ur.rating_id)) as total_actions,
       CASE
           WHEN (COUNT(DISTINCT ul.like_id) + COUNT(DISTINCT ur.rating_id)) > 10 THEN 'Power User'
           WHEN (COUNT(DISTINCT ul.like_id) + COUNT(DISTINCT ur.rating_id)) > 2 THEN 'Active'
           ELSE 'Observer'
       END as status
FROM Users u
LEFT JOIN UserLikes ul ON u.user_id = ul.user_id
LEFT JOIN UserRatings ur ON u.user_id = ur.user_id
GROUP BY u.user_id, u.name
ORDER BY total_actions DESC;

-- 8. Format Popularity View
-- Simple Grouping to compare Movies vs Books vs Music
CREATE OR REPLACE VIEW FormatPopularityView AS
SELECT mt.type_name, COUNT(ul.like_id) as likes
FROM MediaType mt
JOIN Media m ON mt.type_id = m.type_id
LEFT JOIN UserLikes ul ON m.media_id = ul.media_id
GROUP BY mt.type_name
ORDER BY likes DESC;

-- 9. Hidden Gems View
-- Uses HAVING clause to filter high-rated but potentially low-visibility items
CREATE OR REPLACE VIEW HiddenGemsView AS
SELECT m.title, ROUND(AVG(ur.rating_value), 2) as score
FROM Media m
JOIN UserRatings ur ON m.media_id = ur.media_id
GROUP BY m.media_id, m.title
HAVING AVG(ur.rating_value) >= 4.0;

-- 10. System Health View
-- Time-based aggregation from the AuditLog
CREATE OR REPLACE VIEW SystemHealthView AS
SELECT action, COUNT(*) as freq
FROM AuditLog
GROUP BY action
ORDER BY freq DESC;

-- ====================================================================
-- ADVANCED ANALYTICAL VIEWS (Phase 4)
-- ====================================================================

-- 11. GROUPING SETS for Multi-Dimensional Analysis
CREATE OR REPLACE VIEW MediaDistributionAnalysis AS
SELECT
    g.genre_name,
    mt.type_name,
    COUNT(m.media_id) as media_count,
    ROUND(AVG(COALESCE(ur.rating_value, 0)), 2) as avg_rating
FROM Media m
LEFT JOIN MediaGenre mg ON m.media_id = mg.media_id
LEFT JOIN Genre g ON mg.genre_id = g.genre_id
LEFT JOIN MediaType mt ON m.type_id = mt.type_id
LEFT JOIN UserRatings ur ON m.media_id = ur.media_id
GROUP BY GROUPING SETS (
    (g.genre_name),              -- By Genre only
    (mt.type_name),              -- By Type only
    (g.genre_name, mt.type_name), -- By both
    ()                            -- Grand total
);

-- 12. CUBE for User Activity Analysis
CREATE OR REPLACE VIEW UserActivityCube AS
SELECT
    u.name,
    mt.type_name,
    EXTRACT(MONTH FROM ul.liked_on) as month,
    COUNT(ul.like_id) as total_likes
FROM Users u
LEFT JOIN UserLikes ul ON u.user_id = ul.user_id
LEFT JOIN Media m ON ul.media_id = m.media_id
LEFT JOIN MediaType mt ON m.type_id = mt.type_id
WHERE ul.liked_on >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY CUBE(u.name, mt.type_name, EXTRACT(MONTH FROM ul.liked_on));

-- 13. ROLLUP for Hierarchical Genre Stats
CREATE OR REPLACE VIEW GenreHierarchyStats AS
SELECT
    g.genre_name,
    mt.type_name,
    COUNT(m.media_id) as total_items,
    COUNT(DISTINCT ul.user_id) as unique_users,
    ROUND(AVG(ur.rating_value), 2) as avg_rating
FROM Genre g
JOIN MediaGenre mg ON g.genre_id = mg.genre_id
JOIN Media m ON mg.media_id = m.media_id
JOIN MediaType mt ON m.type_id = mt.type_id
LEFT JOIN UserLikes ul ON m.media_id = ul.media_id
LEFT JOIN UserRatings ur ON m.media_id = ur.media_id
GROUP BY ROLLUP(g.genre_name, mt.type_name);