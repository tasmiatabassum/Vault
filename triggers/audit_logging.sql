CREATE OR REPLACE FUNCTION func_audit_list_changes()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO AuditLog (user_id, media_id, action)
    VALUES (NEW.user_id, NEW.media_id, 'Added to ' || NEW.list_type);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_list_insert
AFTER INSERT ON ListItem
FOR EACH ROW
EXECUTE FUNCTION func_audit_list_changes();