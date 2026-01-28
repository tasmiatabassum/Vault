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


def create_user(name, email, password_hash):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (name, email, password_hash, role)
        VALUES (%s, %s, %s, 'user')
        RETURNING user_id;
    """, (name, email, password_hash))

    uid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return uid
