-- ====================================================================
-- BULK OPERATIONS & CURSOR-BASED PROCEDURES
-- CSE4508: RDBMS Programming Lab - Vault Project
-- ====================================================================

-- PROCEDURE: Refresh All User Recommendations (Cursor-Based)
-- Demonstrates: Cursor usage, bulk processing, progress logging
CREATE OR REPLACE PROCEDURE refresh_all_recommendations()
AS $$
DECLARE
    user_cursor CURSOR FOR SELECT user_id FROM Users WHERE role = 'user';
    v_user_id INT;
    v_count INT := 0;
BEGIN
    RAISE NOTICE 'Starting bulk recommendation refresh...';

    OPEN user_cursor;
    LOOP
        FETCH user_cursor INTO v_user_id;
        EXIT WHEN NOT FOUND;

        -- Generate recommendations for this user
        CALL generate_recommendations(v_user_id);
        v_count := v_count + 1;

        -- Log progress every 10 users
        IF v_count % 10 = 0 THEN
            RAISE NOTICE 'Processed % users', v_count;
        END IF;
    END LOOP;
    CLOSE user_cursor;

    -- Log completion
    INSERT INTO AuditLog (action)
    VALUES ('Bulk recommendation refresh completed for ' || v_count || ' users');

    RAISE NOTICE 'Completed! Total users processed: %', v_count;
END;
$$ LANGUAGE plpgsql;

-- ====================================================================
-- ADDITIONAL CURSOR-BASED OPERATIONS (Optional but recommended)
-- ====================================================================

-- PROCEDURE: Bulk Tag Assignment
-- Assigns a tag to multiple media items based on genre
CREATE OR REPLACE PROCEDURE bulk_tag_by_genre(
    p_genre_name VARCHAR,
    p_tag_name VARCHAR
)
AS $$
DECLARE
    media_cursor CURSOR FOR
        SELECT m.media_id
        FROM Media m
        JOIN MediaGenre mg ON m.media_id = mg.media_id
        JOIN Genre g ON mg.genre_id = g.genre_id
        WHERE g.genre_name = p_genre_name;
    v_media_id INT;
    v_count INT := 0;
    v_tag_id INT;
BEGIN
    -- Get or create the tag
    SELECT tag_id INTO v_tag_id FROM Tag WHERE tag_name = p_tag_name;
    IF v_tag_id IS NULL THEN
        INSERT INTO Tag (tag_name) VALUES (p_tag_name) RETURNING tag_id INTO v_tag_id;
    END IF;

    -- Process each media item
    OPEN media_cursor;
    LOOP
        FETCH media_cursor INTO v_media_id;
        EXIT WHEN NOT FOUND;

        -- Add tag (ignore if already exists)
        INSERT INTO MediaTag (media_id, tag_id)
        VALUES (v_media_id, v_tag_id)
        ON CONFLICT DO NOTHING;

        v_count := v_count + 1;
    END LOOP;
    CLOSE media_cursor;

    RAISE NOTICE 'Tagged % media items in genre "%" with tag "%"', v_count, p_genre_name, p_tag_name;
END;
$$ LANGUAGE plpgsql;

-- PROCEDURE: Clean Old Recommendations
-- Removes recommendations older than 30 days
CREATE OR REPLACE PROCEDURE cleanup_old_recommendations()
AS $$
DECLARE
    v_deleted_count INT;
BEGIN
    DELETE FROM Recommendations
    WHERE generated_on < CURRENT_DATE - INTERVAL '30 days';

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;

    INSERT INTO AuditLog (action)
    VALUES ('Cleaned up ' || v_deleted_count || ' old recommendations');

    RAISE NOTICE 'Deleted % old recommendations', v_deleted_count;
END;
$$ LANGUAGE plpgsql;