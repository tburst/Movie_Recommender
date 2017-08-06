# -*- coding: utf-8 -*-
"""
Created on Sun Jul  2 15:55:26 2017

@author: burst
"""

import Imdb_Scraper
import unittest

class TestImdbScraper(unittest.TestCase):
    
    test_movie = Imdb_Scraper.Imdb_Movie(3748528)

    def test_imdb_rating(self):
        self.assertTrue(isinstance(self.test_movie.rating, float))
        
    def test_imdb_title(self):
        self.assertEqual(self.test_movie.title.strip(), "Star Wars: Rogue One")
        
    def test_imdb_rater(self):
        self.assertTrue(isinstance(self.test_movie.rater, int))

    def test_imdb_year(self):
        self.assertEqual(self.test_movie.year, 2016)
    
    def test_imdb_runtime(self):
        self.assertEqual(self.test_movie.runtime, 133)
        
    def test_imdb_genres(self):
        self.assertTrue("Action" in self.test_movie.genres)
        self.assertTrue("Adventure" in self.test_movie.genres)
        self.assertTrue("Sci-Fi" in self.test_movie.genres)
        
    def test_imdb_writer(self):
        self.assertTrue("Chris Weitz" in self.test_movie.writer)
        self.assertTrue("Tony Gilroy" in self.test_movie.writer)

    def test_imdb_director(self):
        self.assertTrue("Gareth Edwards" in self.test_movie.director)

    def test_imdb_country(self):
        self.assertTrue("USA" in self.test_movie.country)

    def test_imdb_similar(self):
        self.assertTrue(80684 in self.test_movie.similars or
                        121766 in self.test_movie.similars or 
                        2488496 in self.test_movie.similars  )
        
    def test_imdb_cast(self):
        self.assertTrue("Felicity Jones" in self.test_movie.cast)
        
    def test_imdb_series(self):
        self.assertTrue(not self.test_movie.is_series)
