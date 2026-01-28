CREATE OR REPLACE VIEW UserActivitySummary AS
SELECT 
    u.user_id,
    u.name,
    (SELECT COUNT(*) FROM UserLikes ul WHERE ul.user_id = u.user_id) + 
    (SELECT COUNT(*) FROM UserRatings ur WHERE ur.user_id = u.user_id) as total_actions,
    -- Divide users into 4 performance quartiles (1 = Top Users)
    NTILE(4) OVER (ORDER BY (
        (SELECT COUNT(*) FROM UserLikes ul WHERE ul.user_id = u.user_id) + 
        (SELECT COUNT(*) FROM UserRatings ur WHERE ur.user_id = u.user_id)
    ) DESC) as user_tier,
    -- Determine the user's "Primary Interest" based on where they have the most ratings
    (SELECT mt.type_name 
     FROM UserRatings ur 
     JOIN Media m ON ur.media_id = m.media_id 
     JOIN MediaType mt ON m.type_id = mt.type_id 
     WHERE ur.user_id = u.user_id 
     GROUP BY mt.type_name 
     ORDER BY COUNT(*) DESC LIMIT 1) as primary_medium
FROM Users u;