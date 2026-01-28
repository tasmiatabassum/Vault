CREATE OR REPLACE PROCEDURE add_media_tag(
    p_user_id INT,
    p_media_id INT,
    p_tag_name VARCHAR
)
AS $$
DECLARE
    v_tag_id INT;
BEGIN
    -- Check if tag exists, or create it (Case insensitive)
    SELECT tag_id INTO v_tag_id FROM Tag WHERE LOWER(tag_name) = LOWER(p_tag_name);
    
    IF v_tag_id IS NULL THEN
        INSERT INTO Tag (tag_name) VALUES (p_tag_name) RETURNING tag_id INTO v_tag_id;
    END IF;

    -- Link the tag to the media
    INSERT INTO MediaTag (media_id, tag_id)
    VALUES (p_media_id, v_tag_id)
    ON CONFLICT (media_id, tag_id) DO NOTHING;

    -- Log it
    INSERT INTO AuditLog (user_id, media_id, action)
    VALUES (p_user_id, p_media_id, 'Added tag: ' || p_tag_name);
END;
$$ LANGUAGE plpgsql;
