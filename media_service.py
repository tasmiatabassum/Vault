import requests

TMDB_API_KEY = "5080e60bc3216eed4e5fb5f485482127"

# These are the official TMDB Genre IDs
GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
    14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
    9648: "Mystery", 10749: "Romance", 878: "Sci-Fi", 10770: "TV Movie",
    53: "Thriller", 10752: "War", 37: "Western"
}

NAME_TO_ID = {v: k for k, v in GENRE_MAP.items()}

def search_external_media(query, media_type, is_genre_search=False):
    results = []
    
    if media_type == "movie":
        if is_genre_search:
            g_id = NAME_TO_ID.get(query, 28)
            # The 'with_genres' parameter ensures the API returns the "Main" genre
            url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&with_genres={g_id}&sort_by=popularity.desc"
        else:
            url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
        
        try:
            response = requests.get(url).json()
            for item in response.get('results', [])[:6]:
                genre_ids = item.get('genre_ids', [])
                # We take the FIRST genre ID as the "Main" one
                genre_name = GENRE_MAP.get(genre_ids[0], "Movie") if genre_ids else "Movie"
                
                results.append({
                    "external_id": str(item['id']),
                    "title": item['title'],
                    "desc": item.get('overview', ''),
                    "year": item.get('release_date', '0000')[:4],
                    "type": "movie",
                    "genre": str(genre_name)
                })
        except Exception as e:
            print(f"Error: {e}")
            
    elif media_type == "book":
        if is_genre_search:
            # Using subject: tag ensures librarian-level accuracy
            url = f"https://openlibrary.org/search.json?subject={query.lower()}&limit=6"
        else:
            url = f"https://openlibrary.org/search.json?q={query}&limit=6"
            
        try:
            response = requests.get(url).json()
            for item in response.get('docs', []):
                genre_display = query if is_genre_search else (item.get('subject', ['Fiction'])[0])
                results.append({
                    "external_id": str(item['key']),
                    "title": item.get('title'),
                    "desc": item.get('subtitle', "No description available."),
                    "year": str(item.get('first_publish_year', '0000')),
                    "type": "book",
                    "genre": str(genre_display)
                })
        except Exception as e:
            print(f"Error: {e}")

    elif media_type == "music":
        url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=6"
        try:
            response = requests.get(url).json()
            for item in response.get('results', []):
                results.append({
                    "external_id": str(item['trackId']),
                    "title": f"{item['trackName']} - {item['artistName']}",
                    "desc": f"Album: {item['collectionName']}",
                    "year": item['releaseDate'][:4],
                    "type": "music",
                    "genre": str(item.get('primaryGenreName', 'Music'))
                })
        except Exception as e:
            print(f"Error: {e}")
            
    return results