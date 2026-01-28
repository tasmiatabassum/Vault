import requests

TMDB_API_KEY = "5080e60bc3216eed4e5fb5f485482127"

GENRE_MAP = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 10751: "Family",
    14: "Fantasy", 36: "History", 27: "Horror", 10402: "Music",
    9648: "Mystery", 10749: "Romance", 878: "Sci-Fi", 10770: "TV Movie",
    53: "Thriller", 10752: "War", 37: "Western"
}

def search_external_media(query, media_type):
    results = []
    
    if media_type == "movie":
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
        response = requests.get(url).json()
        for item in response.get('results', [])[:5]:
            # Logic: Get the first genre ID, map it to a name, or default to 'Movie'
            genre_ids = item.get('genre_ids', [])
            genre_name = GENRE_MAP.get(genre_ids[0], "Movie") if genre_ids else "Movie"

            results.append({
                "external_id": str(item['id']),
                "title": item['title'],
                "desc": item['overview'],
                "year": item.get('release_date', '0000')[:4],
                "type": "movie",
                "genre": genre_name  # <--- CRITICAL FIX
            })
            
    elif media_type == "book":
        url = f"https://openlibrary.org/search.json?q={query}&limit=5"
        response = requests.get(url).json()
        for item in response.get('docs', []):
            subjects = item.get('subject', [])
            
            # IMPROVED GENRE SELECTION LOGIC
            # prioritize specific genres over generic terms
            priority_genres = ['Fantasy', 'Science Fiction', 'Horror', 'Romance', 'Thriller', 'Mystery', 'Historical Fiction', 'Biography']
            
            # Find the first subject that matches our priority list
            genre_name = next((s for s in subjects if s in priority_genres), None)
            
            # If no priority genre found, take the first one, or default to 'Fiction'
            if not genre_name:
                genre_name = subjects[0] if subjects else "Fiction"
            
            results.append({
                "external_id": str(item['key']),
                "title": item.get('title'),
                "desc": item.get('subtitle', "No description available."),
                "year": str(item.get('first_publish_year', '0000')),
                "type": "book",
                "genre": genre_name 
            })

    elif media_type == "music":
        url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=5"
        response = requests.get(url).json()
        for item in response.get('results', []):
            results.append({
                "external_id": str(item['trackId']),
                "title": f"{item['trackName']} - {item['artistName']}",
                "desc": f"Album: {item['collectionName']}",
                "year": item['releaseDate'][:4],
                "type": "music",
                "genre": item.get('primaryGenreName', 'Pop')  # <--- CRITICAL FIX
            })
            
    return results
