from backend.db_connect import get_connection

# --- INTERNAL HELPERS ---

def ensure_media_exists(cur, media_data):
    """
    Internal helper to ensure media, genre, and type records exist in the DB.
    Does NOT record a user action (like or list entry).
    """
    # 1. Ensure the Media Type exists (movie, book, or music)
    cur.execute("SELECT type_id FROM MediaType WHERE type_name = %s", (media_data['type'],))
    type_res = cur.fetchone()
    type_id = type_res[0] if type_res else 1

    # 2. Upsert Media using the title/year unique constraint
    cur.execute("""
        INSERT INTO Media (title, description, release_year, type_id)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (title, release_year) 
        DO UPDATE SET description = EXCLUDED.description
        RETURNING media_id;
    """, (media_data['title'], media_data['desc'], int(media_data['year']), type_id))
    
    media_id = cur.fetchone()[0]

    # 3. Ensure Genre exists and Link it
    genre_name = media_data.get('genre', 'General')
    cur.execute("INSERT INTO Genre (genre_name) VALUES (%s) ON CONFLICT DO NOTHING", (genre_name,))
    
    cur.execute("""
        INSERT INTO MediaGenre (media_id, genre_id)
        SELECT %s, genre_id FROM Genre WHERE genre_name = %s
        ON CONFLICT DO NOTHING;
    """, (media_id, genre_name))

    return media_id

# --- CORE WORKFLOWS ---

def save_user_like(user_id, media_data):
    """
    Saves media and records a user 'Like' (Favorites).
    Returns media_id for rating workflow.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Step 1: Ensure media is in the DB
        media_id = ensure_media_exists(cur, media_data)

        # Step 2: Specifically record the Like
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

def add_to_list_workflow(user_id, media_data, list_type):
    """
    Ensures media exists and then calls SQL Procedure to add to a specific list.
    Handles type constraints (e.g., only books in Readlist).
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Step 1: Ensure media is in the DB
        media_id = ensure_media_exists(cur, media_data)

        # Step 2: Call the SQL Procedure for list management
        cur.execute("CALL add_item_to_list(%s, %s, %s)", (user_id, media_id, list_type))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        # Returns the error message (including the custom SQL RAISE EXCEPTION messages)
        return str(e)
    finally:
        cur.close()
        conn.close()

def submit_rating(user_id, media_id, rating):
    """Calls the SQL Procedure submit_user_rating."""
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

# --- NEW FEATURES (WEEK 8 TAGGING & SIMILARITY) ---

def add_tag_to_media(user_id, media_id, tag_name):
    """Calls the 'add_media_tag' stored procedure."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL add_media_tag(%s, %s, %s)", (user_id, media_id, tag_name))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return str(e)
    finally:
        cur.close()
        conn.close()

def get_similar_media(media_id):
    """Calls the 'get_similar_media' SQL function for recommendations."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT title, type_name, shared_genres FROM get_similar_media(%s)", (media_id,))
        rows = cur.fetchall()
        return [{"title": r[0], "type_name": r[1], "score": r[2]} for r in rows]
    except Exception as e:
        return []
    finally:
        cur.close()
        conn.close()

# --- FETCHING DATA ---

def get_user_likes(user_id):
    """Fetches 'Favorites' (UserLikes table). Includes media_id."""
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT m.media_id, m.title, m.description, m.release_year, mt.type_name
        FROM Media m
        JOIN UserLikes ul ON m.media_id = ul.media_id
        JOIN MediaType mt ON m.type_id = mt.type_id
        WHERE ul.user_id = %s
        ORDER BY ul.liked_on DESC;
    """
    cur.execute(query, (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    return [{"media_id": r[0], "title": r[1], "desc": r[2], "year": r[3], "type_name": r[4]} for r in rows]

def get_user_list_items(user_id, list_type):
    """Fetches items from specific lists (Watchlist, Readlist, etc). Includes media_id."""
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT m.media_id, m.title, m.release_year, mt.type_name, m.description
        FROM ListItem li
        JOIN Media m ON li.media_id = m.media_id
        JOIN MediaType mt ON m.type_id = mt.type_id
        WHERE li.user_id = %s AND li.list_type = %s
        ORDER BY li.added_on DESC;
    """
    cur.execute(query, (user_id, list_type))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    return [{"media_id": r[0], "title": r[1], "year": r[2], "type_name": r[3], "desc": r[4]} for r in rows]

def get_search_gallery():
    """Fetches the MediaSearchGallery SQL View."""
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

# --- ANALYTICS (VIEW CALLS) ---

def get_top_rated_genres():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT genre_name, avg_rating, vote_count FROM TopRatedGenresView LIMIT 5;")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return [{"Genre": r[0], "Avg Rating": float(r[1]), "Votes": r[2]} for r in data]

def get_user_activity_level():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, total_actions, status FROM UserActivityView LIMIT 5;")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return [{"User": r[0], "Actions": r[1], "Status": r[2]} for r in data]

def get_format_popularity():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT type_name, likes FROM FormatPopularityView;")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return [{"Format": r[0], "Total Likes": r[1]} for r in data]

def get_hidden_gems():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT title, score FROM HiddenGemsView LIMIT 5;")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return [{"Title": r[0], "Score": float(r[1])} for r in data]

def get_audit_stats():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT action, freq FROM SystemHealthView LIMIT 5;")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return [{"Action": r[0], "Count": r[1]} for r in data]

def get_media_popularity(media_id):
    """Calls the SQL Function to get the average score."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT calculate_media_score(%s)", (media_id,))
    score = cur.fetchone()
    cur.close()
    conn.close()
    return float(score[0]) if score else 0.0