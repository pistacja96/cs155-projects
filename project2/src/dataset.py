import numpy as np

# movie metadata encoded as indicated in MOVIE_FEATURES
MOVIES = '../data/movies.txt'
# user ratings encoded as user_id, movie_id, rating
RATINGS = '../data/data.txt'

MOVIE_FEATURES = [
    'id',
    'title',
    '', # unknown feature
    'Action',
    'Adventure',
    'Animation',
    'Childrens',
    'Comedy',
    'Crime',
    'Documentary',
    'Drama',
    'Fantasy',
    'Film-Noir',
    'Horror',
    'Musical',
    'Mystery',
    'Romance',
    'Sci-Fi',
    'Thriller',
    'War',
    'Western',
]

class Movie:
    # class property to store dataset once
    _movies = {}

    def __init__(self, id):
        self.id = id
        raw_data = self.movies()[id]
        self.title = raw_data[0]
        self.genres = []
        for genre, indicator in zip(MOVIE_FEATURES[3:], raw_data[2:]):
            if int(indicator):
                self.genres.append(genre)

    @classmethod
    def movies(cls):
        """A dictionary of all movie data.

        The dictionary is keyed on integer movie ids and contains string values mapping to
        MOVIE_FEATURES defined above.

        """
        if not cls._movies:
            cls._movies = {
                int(r[0]): r[1:]
                for r in np.loadtxt(MOVIES, dtype=str, delimiter='\t', encoding='latin1')
            }
        return cls._movies