import requests

TMDB_API_KEY = "5080e60bc3216eed4e5fb5f485482127"

# 1. TMDB Translator (IDs -> Names)
TMDB_GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
    14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
    9648: "Mystery", 10749: "Romance", 878: "Science Fiction",
    10770: "TV Movie", 53: "Thriller", 10752: "War", 37: "Western"
}

# 2. Priority Genre List (We prefer these over "General")
IMPORTANT_BOOK_GENRES = [
    "Fantasy", "Science Fiction", "Sci-Fi", "Dystopian", "Cyberpunk",
    "Horror", "Thriller", "Suspense", "Mystery", "Crime", "Detective",
    "Romance", "Historical Fiction", "Adventure", "Western",
    "Biography", "Autobiography", "Memoir", "History", 
    "Psychology", "Philosophy", "Science", "Technology", "Programming",
    "Business", "Economics", "Finance", "Self-Help", "Health", "Cooking",
    "Art", "Music", "Poetry", "Comics", "Graphic Novels", "Manga",
    "Young Adult", "Children", "Classic", "Humor", "Satire", "Religion",
    "Politics", "Sociology", "Education", "Travel", "True Crime"
]

# 3. Emergency Backup: Guess Genre from Title if API fails
TITLE_KEYWORD_MAP = {
    "hobbit": "Fantasy", "rings": "Fantasy", "potter": "Fantasy", "wizard": "Fantasy",
    "thrones": "Fantasy", "dragon": "Fantasy",
    "star": "Sci-Fi", "space": "Sci-Fi", "planet": "Sci-Fi", "dune": "Sci-Fi",
    "murder": "Mystery", "dead": "Mystery", "girl": "Mystery", "detective": "Mystery",
    "love": "Romance", "heart": "Romance",
    "history": "History", "war": "History",
    "jobs": "Biography", "musk": "Biography", "obama": "Biography", "life": "Biography"
}

def search_external_media(query, media_type):
    results = []
    headers = {"User-Agent": "VaultApp/1.0 (Student Project)"}

    try:
        # --- MOVIES (TMDB) ---
        if media_type == "movie":
            url = "https://api.themoviedb.org/3/search/movie"
            params = {"api_key": TMDB_API_KEY, "query": query}
            response = requests.get(url, params=params, headers=headers).json()
            
            for item in response.get('results', [])[:5]:
                g_ids = item.get('genre_ids', [])
                genre_val = TMDB_GENRE_MAP.get(g_ids[0], "Movie") if g_ids else "Movie"

                results.append({
                    "external_id": str(item['id']),
                    "title": item['title'],
                    "desc": item.get('overview', 'No description available.'),
                    "year": item.get('release_date', '0000')[:4],
                    "type": "movie",
                    "genre": genre_val
                })
                
        # --- BOOKS (OPEN LIBRARY) ---
        elif media_type == "book":
            url = "https://openlibrary.org/search.json"
            # FIX: We strictly ask for 'subject' field to prevent empty results
            params = {
                "q": query, 
                "limit": 5, 
                "fields": "key,title,author_name,first_publish_year,subject"
            }
            response = requests.get(url, params=params, headers=headers).json()
            
            for item in response.get('docs', []):
                genre_val = "Literature" # Default
                
                # A. Try API Subjects
                subjects = item.get('subject', [])
                
                # Smart Filter: Check priority list
                found_specific = False
                if subjects:
                    for priority in IMPORTANT_BOOK_GENRES:
                        for subj in subjects:
                            if priority.lower() in subj.lower():
                                genre_val = priority
                                found_specific = True
                                break
                        if found_specific:
                            break
                    if not found_specific:
                        genre_val = subjects[0] # Take first available if no priority match

                # B. Emergency Fallback: Check Title Keywords if API returned nothing
                if not subjects or genre_val == "Literature":
                    title_lower = item.get('title', '').lower()
                    for key, val in TITLE_KEYWORD_MAP.items():
                        if key in title_lower:
                            genre_val = val
                            break

                # Extract Author
                authors = item.get('author_name', ['Unknown Author'])
                desc_text = f"Written by {', '.join(authors[:2])}."

                results.append({
                    "external_id": item['key'],
                    "title": item.get('title', 'Unknown Title'),
                    "desc": desc_text,
                    "year": str(item.get('first_publish_year', '0000')),
                    "type": "book",
                    "genre": genre_val
                })

        # --- MUSIC (ITUNES) ---
        elif media_type == "music":
            url = "https://itunes.apple.com/search"
            params = {"term": query, "entity": "song", "limit": 5}
            response = requests.get(url, params=params, headers=headers).json()
            
            for item in response.get('results', []):
                results.append({
                    "external_id": str(item['trackId']),
                    "title": f"{item['trackName']} - {item['artistName']}",
                    "desc": f"Album: {item['collectionName']}",
                    "year": item.get('releaseDate', '0000')[:4],
                    "type": "music",
                    "genre": item.get('primaryGenreName', 'Music')
                })
                
    except Exception as e:
        print(f"API Error: {e}")
        return []

    return results