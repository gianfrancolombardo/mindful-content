import requests
from typing import List, Dict

class MovieAPI:
    def __init__(self, token: str):
        """Initialize MovieAPI with the given token."""
        self.base_url = "https://api.themoviedb.org/3/"
        self.token = token

    def make_request(self, endpoint: str) -> Dict[str, str]:
        """Make a GET request to the given endpoint and return the JSON response."""
        headers = {"Authorization": "Bearer " + self.token}
        response = requests.get(self.base_url + endpoint, headers=headers)
        response.raise_for_status()
        return response.json()

    def fetch_movies(self, lang: str = 'en-US') -> List[Dict[str, str]]:
        """Fetch popular movies and return a list of dictionaries with movie details."""
        fields = ['id', 'title', 'release_date', 'poster_path', 'vote_average']
        data = self.make_request(f"discover/movie?include_adult=false&include_video=false&language={lang}&page=1&sort_by=popularity.desc&primary_release_date.lte=2022-01-01&primary_release_date.gte=2021-01-01")
        movies = []

        for movie in data['results']:
            movie_data = {field: movie.get(field, None) for field in fields}
            if 'release_date' in movie_data and movie_data['release_date']:
                movie_data['year'] = movie_data['release_date'].split('-')[0]
            movies.append(movie_data)

        return movies
    
    def fetch_movie_details(self, movie_id: str, lang: str = 'en-US') -> Dict[str, str]:
        """Fetch the details of a specific movie and return a dictionary with the details."""
        return self.make_request(f"movie/{movie_id}?language={lang}")

    def fetch_external_ids(self, movie_id: str) -> Dict[str, str]:
        """Fetch the external IDs of a movie and return a dictionary with the IDs."""
        return self.make_request(f"movie/{movie_id}/external_ids")