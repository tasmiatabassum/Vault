import bcrypt
from backend.db_connect import get_connection


def get_user_by_email(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, name, email, password_hash, role
        FROM users
        WHERE email = %s
    """, (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user


def verify_password(plain_password, stored_hash):
    """
    Check a plain password against a stored hash.
    Supports both bcrypt hashes (new accounts) and plaintext (legacy accounts).
    Legacy plaintext passwords are automatically migrated to bcrypt on login.
    """
    if stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$"):
        # Proper bcrypt hash
        return bcrypt.checkpw(plain_password.encode("utf-8"), stored_hash.encode("utf-8"))
    else:
        # Legacy plaintext — compare directly, then migrate
        if plain_password == stored_hash:
            _migrate_password_hash(plain_password, stored_hash)
            return True
        return False


def _migrate_password_hash(plain_password, old_hash):
    """Silently upgrade a plaintext password to bcrypt on successful login."""
    new_hash = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE password_hash = %s",
            (new_hash, old_hash)
        )
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close()
        conn.close()


def create_user(name, email, password):
    """Hash the password before storing it."""
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO users (name, email, password_hash, role)
            VALUES (%s, %s, %s, 'user')
            RETURNING user_id;
        """, (name, email, password_hash))
        uid = cur.fetchone()[0]
        conn.commit()
        return uid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()