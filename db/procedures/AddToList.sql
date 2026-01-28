-- db/procedures/AddToList.sql

CREATE OR REPLACE PROCEDURE add_item_to_list(
    p_user_id INT, 
    p_media_id INT, 
    p_list_type VARCHAR
)
AS $$
BEGIN
    -- Attempt to insert the item into the specified list
    INSERT INTO ListItem (user_id, media_id, list_type)
    VALUES (p_user_id, p_media_id, p_list_type);
    
    -- Log this action in the audit trail (Good for Nashat's Role)
    INSERT INTO AuditLog (user_id, media_id, action)
    VALUES (p_user_id, p_media_id, 'Added to ' || p_list_type);

EXCEPTION
    WHEN unique_violation THEN
        -- Gracefully handle duplicates without crashing the app
        RAISE NOTICE 'Item is already in your %', p_list_type;
END;
$$ LANGUAGE plpgsql;