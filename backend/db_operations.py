from backend.db_connect import get_connection


# --- INTERNAL HELPERS ---

def ensure_media_exists(cur, media_data):
    """
    Internal helper to ensure media, genre, and type records exist in the DB.
    Does NOT record a user action (like or list entry).
    """
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

    return media_id


# --- CORE WORKFLOWS ---

def save_user_like(user_id, media_data):
    """
    Saves media and records a user 'Like' (Favorites).
    Returns media_id for the rating workflow.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        media_id = ensure_media_exists(cur, media_data)
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


def like_existing_media(user_id, media_id):
    """
    Records a Like for a media item that already exists in the DB.
    Used when liking from Recommendations (avoids re-running ensure_media_exists).
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO UserLikes (user_id, media_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (user_id, media_id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return str(e)
    finally:
        cur.close()
        conn.close()


def add_to_list_workflow(user_id, media_data, list_type):
    """
    Ensures media exists and then calls the SQL Procedure to add to a specific list.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        media_id = ensure_media_exists(cur, media_data)
        cur.execute("CALL add_item_to_list(%s, %s, %s)", (user_id, media_id, list_type))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return str(e)
    finally:
        cur.close()
        conn.close()


def add_existing_to_list(user_id, media_id, list_type):
    """
    Adds an already-existing media item to a list by media_id.
    Used when acting on Recommendations (avoids re-running ensure_media_exists).
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
    """Calls the 'get_similar_media' SQL function."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT title, type_name, similarity_score FROM get_similar_media(%s)", (media_id,))
        rows = cur.fetchall()
        return [{"title": r[0], "type_name": r[1], "score": r[2]} for r in rows]
    except Exception as e:
        print(f"Error in similarity: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def generate_recommendations_for_user(user_id):
    """Calls generate_recommendations for a single user. Used by the frontend."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL generate_recommendations(%s)", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return str(e)
    finally:
        cur.close()
        conn.close()


# --- FETCHING DATA ---

def get_user_likes(user_id):
    """Fetches Favorites (UserLikes table). Includes media_id."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT m.media_id, m.title, m.description, m.release_year, mt.type_name
            FROM Media m
            JOIN UserLikes ul ON m.media_id = ul.media_id
            JOIN MediaType mt ON m.type_id = mt.type_id
            WHERE ul.user_id = %s
            ORDER BY ul.liked_on DESC;
        """, (user_id,))
        rows = cur.fetchall()
        return [{"media_id": r[0], "title": r[1], "desc": r[2], "year": r[3], "type_name": r[4]} for r in rows]
    finally:
        cur.close()
        conn.close()


def get_user_list_items(user_id, list_type):
    """Fetches items from a specific list. Includes media_id."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT m.media_id, m.title, m.release_year, mt.type_name, m.description
            FROM ListItem li
            JOIN Media m ON li.media_id = m.media_id
            JOIN MediaType mt ON m.type_id = mt.type_id
            WHERE li.user_id = %s AND li.list_type = %s
            ORDER BY li.added_on DESC;
        """, (user_id, list_type))
        rows = cur.fetchall()
        return [{"media_id": r[0], "title": r[1], "year": r[2], "type_name": r[3], "desc": r[4]} for r in rows]
    finally:
        cur.close()
        conn.close()


def get_search_gallery():
    """Fetches the MediaSearchGallery SQL View."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT media_id, title, release_year, type_name, genres FROM MediaSearchGallery;")
        rows = cur.fetchall()
        return [{"ID": r[0], "Title": r[1], "Year": r[2], "Type": r[3], "Genres": r[4]} for r in rows]
    except Exception:
        return []
    finally:
        cur.close()
        conn.close()


def get_user_recommendations(user_id):
    """Fetch personalized recommendations for a user."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT m.media_id, m.title, m.description, m.release_year,
                   mt.type_name, r.score,
                   COALESCE(STRING_AGG(DISTINCT g.genre_name, ', '), 'General') AS genres
            FROM Recommendations r
            JOIN Media m ON r.media_id = m.media_id
            JOIN MediaType mt ON m.type_id = mt.type_id
            LEFT JOIN MediaGenre mg ON m.media_id = mg.media_id
            LEFT JOIN Genre g ON mg.genre_id = g.genre_id
            WHERE r.user_id = %s
            GROUP BY m.media_id, m.title, m.description, m.release_year, mt.type_name, r.score
            ORDER BY r.score DESC
            LIMIT 10;
        """, (user_id,))
        rows = cur.fetchall()
        return [{
            "media_id": r[0], "title": r[1], "desc": r[2],
            "year": r[3], "type_name": r[4], "score": float(r[5]), "genres": r[6]
        } for r in rows]
    finally:
        cur.close()
        conn.close()


def get_user_theme_weights(user_id):
    """Get user's genre/tag preferences."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM compute_user_theme_weights(%s)", (user_id,))
        rows = cur.fetchall()
        return [{"theme": r[0], "weight": int(r[1]), "category": r[2]} for r in rows]
    finally:
        cur.close()
        conn.close()


# --- ANALYTICS ---

def get_top_rated_genres():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT genre_name, avg_rating, vote_count FROM TopRatedGenresView LIMIT 5;")
        data = cur.fetchall()
        return [{"Genre": r[0], "Avg Rating": float(r[1]), "Votes": r[2]} for r in data]
    finally:
        cur.close()
        conn.close()


def get_user_activity_level():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT name, total_actions, status FROM UserActivityView LIMIT 5;")
        data = cur.fetchall()
        return [{"User": r[0], "Actions": r[1], "Status": r[2]} for r in data]
    finally:
        cur.close()
        conn.close()


def get_format_popularity():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT type_name, likes FROM FormatPopularityView;")
        data = cur.fetchall()
        return [{"Format": r[0], "Total Likes": r[1]} for r in data]
    finally:
        cur.close()
        conn.close()


def get_hidden_gems():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT title, score FROM HiddenGemsView LIMIT 5;")
        data = cur.fetchall()
        return [{"Title": r[0], "Score": float(r[1])} for r in data]
    finally:
        cur.close()
        conn.close()


def get_audit_stats():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT action, freq FROM SystemHealthView LIMIT 5;")
        data = cur.fetchall()
        return [{"Action": r[0], "Count": r[1]} for r in data]
    finally:
        cur.close()
        conn.close()


def get_media_popularity(media_id):
    """Calls the SQL Function to get the average score."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT calculate_media_score(%s)", (media_id,))
        score = cur.fetchone()
        return float(score[0]) if score else 0.0
    finally:
        cur.close()
        conn.close()


def get_db_stats():
    """Returns key counts for the admin dashboard. Avoids raw DB calls in the frontend."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM Users WHERE role = 'user'")
        user_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM Media")
        media_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM UserLikes")
        likes_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM UserRatings")
        ratings_count = cur.fetchone()[0]
        return {
            "users": user_count,
            "media": media_count,
            "likes": likes_count,
            "ratings": ratings_count,
        }
    finally:
        cur.close()
        conn.close()


def get_full_audit_log():
    """Returns the full audit log for the admin panel."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT al.log_id, u.name AS user_name, m.title AS media_title,
                   al.action, al.action_time
            FROM AuditLog al
            LEFT JOIN Users u ON al.user_id = u.user_id
            LEFT JOIN Media m ON al.media_id = m.media_id
            ORDER BY al.action_time DESC
            LIMIT 100;
        """)
        rows = cur.fetchall()
        return [{"ID": r[0], "User": r[1], "Media": r[2], "Action": r[3], "Time": r[4]} for r in rows]
    finally:
        cur.close()
        conn.close()


def refresh_all_recommendations():
    """Admin function to regenerate all recommendations."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL refresh_all_recommendations()")
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        return str(e)
    finally:
        cur.close()
        conn.close()


def get_advanced_analytics(view_name):
    """Fetch data from advanced analytical views."""
    valid_views = {
        'distribution': 'MediaDistributionAnalysis',
        'activity_cube': 'UserActivityCube',
        'genre_hierarchy': 'GenreHierarchyStats',
    }

    if view_name not in valid_views:
        raise ValueError(f"Unknown analytics view: '{view_name}'")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT * FROM {valid_views[view_name]} LIMIT 50")
        rows = cur.fetchall()
        # cur.description must be read before closing
        columns = [desc[0] for desc in cur.description]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"Analytics error for '{view_name}': {e}")
        return []
    finally:
        cur.close()
        conn.close()