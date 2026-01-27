import requests

TMDB_API_KEY = "5080e60bc3216eed4e5fb5f485482127"

def search_external_media(query, media_type):
    results = []
    
    if media_type == "movie":
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
        response = requests.get(url).json()
        for item in response.get('results', [])[:5]: # Limit to 5
            results.append({
                "external_id": str(item['id']),
                "title": item['title'],
                "desc": item['overview'],
                "year": item.get('release_date', '0000')[:4],
                "type": "movie"
            })
            
    elif media_type == "book":
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}"
        response = requests.get(url).json()
        for item in response.get('items', [])[:5]:
            info = item.get('volumeInfo', {})
            results.append({
                "external_id": item['id'],
                "title": info.get('title'),
                "desc": info.get('description', '')[:200],
                "year": info.get('publishedDate', '0000')[:4],
                "type": "book"
            })

    elif media_type == "music":
        # iTunes Search API
        url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=5"
        response = requests.get(url).json()
        for item in response.get('results', []):
            results.append({
                "external_id": str(item['trackId']),
                "title": f"{item['trackName']} - {item['artistName']}",
                "desc": f"Album: {item['collectionName']}",
                "year": item['releaseDate'][:4],
                "type": "music"
            })
    return results