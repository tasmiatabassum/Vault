CREATE OR REPLACE FUNCTION func_validate_rating()
RETURNS TRIGGER AS $$
BEGIN

    IF NEW.rating_value < 1 OR NEW.rating_value > 5 THEN
        RAISE EXCEPTION 'Invalid rating %: Must be between 1 and 5', NEW.rating_value;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_rating
BEFORE INSERT ON UserRatings
FOR EACH ROW
EXECUTE FUNCTION func_validate_rating();