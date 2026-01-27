from backend.db_connect import get_connection

def save_user_like(user_id, media_data):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # 1. Get type_id (Ensure you have 'music', 'book', 'movie' in MediaType table) [cite: 65, 160]
        cur.execute("SELECT type_id FROM MediaType WHERE type_name = %s", (media_data['type'],))
        type_res = cur.fetchone()
        if not type_res:
            # Fallback if the table isn't seeded
            cur.execute("INSERT INTO MediaType (type_name) VALUES (%s) RETURNING type_id", (media_data['type'],))
            type_id = cur.fetchone()[0]
        else:
            type_id = type_res[0]

        # 2. Upsert Media
        # This requires the UNIQUE (title, release_year) constraint in Postgres
        cur.execute("""
            INSERT INTO Media (title, description, release_year, type_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (title, release_year) 
            DO UPDATE SET description = EXCLUDED.description
            RETURNING media_id;
        """, (media_data['title'], media_data['desc'], int(media_data['year']), type_id))
        
        media_id = cur.fetchone()[0]

        # 3. Insert Like
        cur.execute("""
            INSERT INTO UserLikes (user_id, media_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (user_id, media_id))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()