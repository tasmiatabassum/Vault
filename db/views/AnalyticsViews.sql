-- ====================================================================
-- VAULT ANALYTICS VIEWS
-- CSE4508: RDBMS Programming Lab
-- ====================================================================

-- 1. Top Rated Genres
-- Aggregates average rating per genre using JOINs
CREATE OR REPLACE VIEW TopRatedGenresView AS
SELECT g.genre_name,
       ROUND(AVG(ur.rating_value), 2) AS avg_rating,
       COUNT(ur.rating_id)            AS vote_count
FROM Genre g
JOIN MediaGenre mg ON g.genre_id = mg.genre_id
JOIN UserRatings ur ON mg.media_id = ur.media_id
GROUP BY g.genre_name
HAVING COUNT(ur.rating_id) > 0
ORDER BY avg_rating DESC;

-- 2. User Activity Level
-- Categorizes users by total engagement using CASE
CREATE OR REPLACE VIEW UserActivityView AS
SELECT u.name,
       (COUNT(DISTINCT ul.like_id) + COUNT(DISTINCT ur.rating_id)) AS total_actions,
       CASE
           WHEN (COUNT(DISTINCT ul.like_id) + COUNT(DISTINCT ur.rating_id)) > 10 THEN 'Power User'
           WHEN (COUNT(DISTINCT ul.like_id) + COUNT(DISTINCT ur.rating_id)) > 2  THEN 'Active'
           ELSE 'Observer'
       END AS status
FROM Users u
LEFT JOIN UserLikes ul ON u.user_id = ul.user_id
LEFT JOIN UserRatings ur ON u.user_id = ur.user_id
GROUP BY u.user_id, u.name
ORDER BY total_actions DESC;

-- 3. Format Popularity
-- Compares total likes across movie / book / music
CREATE OR REPLACE VIEW FormatPopularityView AS
SELECT mt.type_name,
       COUNT(ul.like_id) AS likes
FROM MediaType mt
JOIN Media m ON mt.type_id = m.type_id
LEFT JOIN UserLikes ul ON m.media_id = ul.media_id
GROUP BY mt.type_name
ORDER BY likes DESC;

-- 4. Hidden Gems
-- High-rated media (avg >= 4.0) that may be under-discovered
CREATE OR REPLACE VIEW HiddenGemsView AS
SELECT m.title,
       ROUND(AVG(ur.rating_value), 2) AS score
FROM Media m
JOIN UserRatings ur ON m.media_id = ur.media_id
GROUP BY m.media_id, m.title
HAVING AVG(ur.rating_value) >= 4.0;

-- 5. System Health
-- Action frequency summary from the AuditLog
CREATE OR REPLACE VIEW SystemHealthView AS
SELECT action,
       COUNT(*) AS freq
FROM AuditLog
GROUP BY action
ORDER BY freq DESC;

-- ====================================================================
-- ADVANCED ANALYTICAL VIEWS
-- ====================================================================

-- 6. GROUPING SETS — Multi-Dimensional Media Distribution
CREATE OR REPLACE VIEW MediaDistributionAnalysis AS
SELECT g.genre_name,
       mt.type_name,
       COUNT(m.media_id)                              AS media_count,
       ROUND(AVG(COALESCE(ur.rating_value, 0)), 2)   AS avg_rating
FROM Media m
LEFT JOIN MediaGenre mg  ON m.media_id  = mg.media_id
LEFT JOIN Genre g        ON mg.genre_id = g.genre_id
LEFT JOIN MediaType mt   ON m.type_id   = mt.type_id
LEFT JOIN UserRatings ur ON m.media_id  = ur.media_id
GROUP BY GROUPING SETS (
    (g.genre_name),
    (mt.type_name),
    (g.genre_name, mt.type_name),
    ()
);

-- 7. CUBE — User Activity by Type and Month
CREATE OR REPLACE VIEW UserActivityCube AS
SELECT u.name,
       mt.type_name,
       EXTRACT(MONTH FROM ul.liked_on) AS month,
       COUNT(ul.like_id)               AS total_likes
FROM Users u
LEFT JOIN UserLikes ul   ON u.user_id   = ul.user_id
LEFT JOIN Media m        ON ul.media_id = m.media_id
LEFT JOIN MediaType mt   ON m.type_id   = mt.type_id
WHERE ul.liked_on >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY CUBE (u.name, mt.type_name, EXTRACT(MONTH FROM ul.liked_on));

-- 8. ROLLUP — Hierarchical Genre Statistics
CREATE OR REPLACE VIEW GenreHierarchyStats AS
SELECT g.genre_name,
       mt.type_name,
       COUNT(m.media_id)               AS total_items,
       COUNT(DISTINCT ul.user_id)      AS unique_users,
       ROUND(AVG(ur.rating_value), 2)  AS avg_rating
FROM Genre g
JOIN MediaGenre mg  ON g.genre_id   = mg.genre_id
JOIN Media m        ON mg.media_id  = m.media_id
JOIN MediaType mt   ON m.type_id    = mt.type_id
LEFT JOIN UserLikes ul   ON m.media_id = ul.media_id
LEFT JOIN UserRatings ur ON m.media_id = ur.media_id
GROUP BY ROLLUP (g.genre_name, mt.type_name);