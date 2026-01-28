from backend.db_connect import get_connection

def save_user_like(user_id, media_data):
    """
    Saves media, ensures the genre is linked, and records a user 'Like'.
    RETURNS: media_id (int) - Critical for subsequent rating calls.
    Fulfills Week 8 requirement for partial workflow demo.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # 1. Ensure the Media Type exists (movie, book, or music)
        cur.execute("SELECT type_id FROM MediaType WHERE type_name = %s", (media_data['type'],))
        type_res = cur.fetchone()
        type_id = type_res[0] if type_res else 1

        # 2. Upsert Media using the title/year unique constraint
        # We assume media_data['desc'] matches your API keys. Adjust if needed.
        cur.execute("""
            INSERT INTO Media (title, description, release_year, type_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (title, release_year) 
            DO UPDATE SET description = EXCLUDED.description
            RETURNING media_id;
        """, (media_data['title'], media_data['desc'], int(media_data['year']), type_id))
        
        media_id = cur.fetchone()[0]

        # 3. LINK GENRE (The fix for the "General" issue)
        # Fetch the genre name from the API data, defaulting to 'General' if missing
        genre_name = media_data.get('genre', 'General')
        
        # Ensure the genre exists in the Genre table
        cur.execute("INSERT INTO Genre (genre_name) VALUES (%s) ON CONFLICT DO NOTHING", (genre_name,))
        
        # Link the media to the genre in the junction table
        cur.execute("""
            INSERT INTO MediaGenre (media_id, genre_id)
            SELECT %s, genre_id FROM Genre WHERE genre_name = %s
            ON CONFLICT DO NOTHING;
        """, (media_id, genre_name))

        # 4. Record the Like - This triggers the 'after_media_like' SQL Trigger
        cur.execute("""
            INSERT INTO UserLikes (user_id, media_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (user_id, media_id))
        
        conn.commit()
        
        # --- CRITICAL RETURN FOR FRONTEND RATING ---
        return media_id 
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def get_user_likes(user_id):
    """Fetches user library via multi-table JOIN."""
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
    
    results = []
    for row in rows:
        results.append({
            "title": row[0], "description": row[1],
            "release_year": row[2], "type_name": row[3]
        })
    cur.close()
    conn.close()
    return results

def submit_rating(user_id, media_id, rating):
    """
    Calls the SQL Procedure submit_user_rating.
    Fulfills Nashat's role for procedural workflow and logging.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Calling the SQL PROCEDURE defined in your schema
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
    """
    Fetches media with aggregated genres from the MediaSearchGallery View.
    Fulfills Mrittika's role in complex relational data display.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Querying the View just like a table
        cur.execute("SELECT media_id, title, release_year, type_name, genres FROM MediaSearchGallery;")
        rows = cur.fetchall()
        
        # Format the result for easy display in the dataframe
        results = []
        for row in rows:
            results.append({
                "ID": row[0],
                "Title": row[1],
                "Year": row[2],
                "Type": row[3],
                "Genres": row[4]
            })
        return results
    except Exception as e:
        print(f"View Fetch Error: {e}")
        return []
    finally:
        cur.close()
        conn.close()

def add_to_list_workflow(user_id, media_id, list_type):
    """
    Calls the SQL Procedure to add an item to a specific list.
    Fulfills Nashat's role for procedural workflow logic.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL add_item_to_list(%s, %s, %s)", (user_id, media_id, list_type))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return str(e)
    finally:
        cur.close()
        conn.close()

def get_media_popularity(media_id):
    """
    Calls the SQL Function to get the average score.
    Fulfills Tasmia's role for complex data calculation.
    """
    conn = get_connection()
    cur = conn.cursor()
    # Calling the SQL FUNCTION using 'SELECT'
    cur.execute("SELECT calculate_media_score(%s)", (media_id,))
    score = cur.fetchone()
    cur.close()
    conn.close()
    return float(score[0]) if score else 0.0