from backend.db_connect import get_connection

def save_user_like(user_id, media_data):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT type_id FROM MediaType WHERE type_name = %s", (media_data['type'],))
        type_res = cur.fetchone()
        type_id = type_res[0] if type_res else 1

        cur.execute("""
            INSERT INTO Media (title, description, release_year, type_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (title, release_year) 
            DO UPDATE SET description = EXCLUDED.description
            RETURNING media_id;
        """, (media_data['title'], media_data['desc'], int(media_data['year']), type_id))
        
        media_id = cur.fetchone()[0]
        genre_name = media_data.get('genre', 'General')
        cur.execute("INSERT INTO Genre (genre_name) VALUES (%s) ON CONFLICT DO NOTHING", (genre_name,))
        
        cur.execute("""
            INSERT INTO MediaGenre (media_id, genre_id)
            SELECT %s, genre_id FROM Genre WHERE genre_name = %s
            ON CONFLICT DO NOTHING;
        """, (media_id, genre_name))

        cur.execute("""
            INSERT INTO UserLikes (user_id, media_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (user_id, media_id))
        
        conn.commit()
        return media_id 
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_user_likes(user_id):
    conn = get_connection()
    cur = conn.cursor()
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
    results = [{"title": r[0], "description": r[1], "release_year": r[2], "type_name": r[3]} for r in rows]
    cur.close()
    conn.close()
    return results

def submit_rating(user_id, media_id, rating):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL submit_user_rating(%s, %s, %s)", (user_id, media_id, rating))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return str(e)
    finally:
        cur.close()
        conn.close()

def get_search_gallery():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT media_id, title, release_year, type_name, genres FROM MediaSearchGallery;")
        rows = cur.fetchall()
        return [{"ID": r[0], "Title": r[1], "Year": r[2], "Type": r[3], "Genres": r[4]} for r in rows]
    except Exception as e:
        return []
    finally:
        cur.close()
        conn.close()

# --- ADDED FUNCTIONS FOR GENRE SEARCH ---

def fetch_all_genres():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT genre_name FROM Genre ORDER BY genre_name ASC")
        return [row[0] for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

def search_media_by_genre(genre_name):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM get_media_by_genre(%s)", (genre_name,))
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()