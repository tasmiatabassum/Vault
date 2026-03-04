-- ====================================================================
-- PROCEDURE: add_item_to_list
-- Adds a media item to a user's list (watchlist / readlist / playlist).
-- Duplicate insertions are silently ignored.
-- AuditLog is written by the after_list_insert trigger — NOT here.
-- ====================================================================

CREATE OR REPLACE PROCEDURE add_item_to_list(
    p_user_id  INT,
    p_media_id INT,
    p_list_type VARCHAR
)
AS $$
BEGIN
    INSERT INTO ListItem (user_id, media_id, list_type)
    VALUES (p_user_id, p_media_id, p_list_type);

EXCEPTION
    WHEN unique_violation THEN
        -- Item already in list — silently ignore
        RAISE NOTICE 'Item is already in your %', p_list_type;
END;
$$ LANGUAGE plpgsql;