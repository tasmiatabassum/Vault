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
