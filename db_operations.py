from backend.db_connect import get_connection

def save_user_like(user_id, media_data):
    """
    Saves a media item to the database and records a user 'Like'.
    Uses 'Upsert' logic to prevent duplicate media entries[cite: 64, 68].
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # 1. Get type_id (Ensure you have 'music', 'book', 'movie' in MediaType table) [cite: 65, 160]
        cur.execute("SELECT type_id FROM MediaType WHERE type_name = %s", (media_data['type'],))
        type_res = cur.fetchone()
        
        if not type_res:
            # Fallback if the table isn't seeded [cite: 160, 162]
            cur.execute("INSERT INTO MediaType (type_name) VALUES (%s) RETURNING type_id", (media_data['type'],))
            type_id = cur.fetchone()[0]
        else:
            type_id = type_res[0]

        # 2. Upsert Media using the UNIQUE (title, release_year) constraint [cite: 64, 131]
        cur.execute("""
            INSERT INTO Media (title, description, release_year, type_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (title, release_year) 
            DO UPDATE SET description = EXCLUDED.description
            RETURNING media_id;
        """, (media_data['title'], media_data['desc'], int(media_data['year']), type_id))
        
        media_id = cur.fetchone()[0]

        # 3. Insert Like into UserLikes table [cite: 68, 76]
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

def get_user_likes(user_id):
    """
    Fetches all media liked by a specific user using a multi-table JOIN[cite: 280].
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # Mrittika's implementation: joining Media, UserLikes, and MediaType [cite: 64, 65, 68]
    query = """
        SELECT m.title, m.description, m.release_year, mt.type_name
        FROM Media m
        JOIN UserLikes ul ON m.media_id = ul.media_id
        JOIN MediaType mt ON m.type_id = mt.type_id
        WHERE ul.user_id = %s
        ORDER BY ul.liked_on DESC;
    """
    
    cur.execute(query, (user_id,))
    rows = cur.fetchall()
    
    # Organize data for the dashboard [cite: 54, 280]
    results = []
    for row in rows:
        results.append({
            "title": row[0],
            "description": row[1],
            "release_year": row[2],
            "type_name": row[3]
        })
    
    cur.close()
    conn.close()
    return results
