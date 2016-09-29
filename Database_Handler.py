# -*- coding: utf-8 -*-
"""
Created on Thu Sep 29 16:00:46 2016

@author: Tobi
"""


import sqlite3


class Database_Movies:
    
    
    def __init__(self,user_name):
        self.user_name = user_name
        self.conn = sqlite3.connect('Movie_Database.db')
        
        
        #Create database structure if not already there        
        self.conn.execute(''' CREATE TABLE IF NOT EXISTS Movie_Country (imdbID NUMERIC,
                                                                        Country_imdb VARCHAR(30),
                                                                        PRIMARY KEY (imdbID, Country_imdb))  ''')
        self.conn.execute(''' CREATE TABLE IF NOT EXISTS Movie_Director (imdbID NUMERIC,
                                                                         Director_imdb VARCHAR(30),
                                                                		  PRIMARY KEY (imdbID, Director_imdb))''')
        self.conn.execute(''' CREATE TABLE IF NOT EXISTS Movie_Genre (imdbID NUMERIC,
                                                                      Genre_imdb VARCHAR(30),
                                                                      PRIMARY KEY (imdbID, Genre_imdb))''')
        self.conn.execute(''' CREATE TABLE IF NOT EXISTS Movie_Similar(imdbID NUMERIC,
                                                                       SimilarMovieID_imdb NUMERIC,
                                                                       PRIMARY KEY (imdbID, SimilarMovieID_imdb ))''')
        self.conn.execute(''' CREATE TABLE IF NOT EXISTS Movie_Star(imdbID NUMERIC,
                                                                    Star_imdb VARCHAR(30),
                                                                    PRIMARY KEY (imdbID, Star_imdb))''')
        self.conn.execute(''' CREATE TABLE IF NOT EXISTS Movie_Writer(imdbID NUMERIC,
                                                                      Writer_imdb VARCHAR(30),
                                                                      PRIMARY KEY (imdbID, Writer_imdb))''')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS Movie_imdbData(imdbID NUMERIC PRIMARY KEY,
                                                                       Title_imdb VARCHAR(30),
                                                                       Rater_imdb NUMERIC,
                                                                       Release_imdb NUMERIC,
                                                                       Runtime_imdb NUMERIC,
                                                                       Rating_imdb Numeric)''')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS Own_Rating (imdbID NUMERIC,
                                                                    Personal_Rating NUMERIC,
                                                                    Rater VARCHAR(30), 
                                                                    FilmempfehlungID NUMERIC,
                                                                    PRIMARY KEY (imdbID, Rater  ))''')
        self.conn.execute('''CREATE TABLE IF NOT EXISTS Potential_Movies(imdbID NUMERIC,
                                                                         Title_imdb VARCHAR(30),
                                                                         Calculated_Rating NUMERIC,
                                                                         Rater VARCHAR(30),
                                                                         PRIMARY KEY (imdbID,Rater))''')
        
        self.get_allRatedMoviesIdList()
        self.get_allRatedMoviesDict()
        self.get_allPotentialMoviesList()


    def store_FilmempfMovie_InDatabase(self,imdb_id, personal_rating, filmempf_id):
        #delete from potential new movies
        self.conn.execute('''DELETE FROM Potential_Movies WHERE imdbID = ? AND Rater = ?''', (imdb_id, self.user_name))
        #store personal rating in database
        self.conn.execute('''INSERT OR REPLACE INTO Own_Rating (imdbID, 
                                                  Personal_Rating,
                                                  Rater,
                                                  FilmempfehlungID
                                                  )
                                                  VALUES (?,?,?,?)''',           
                                                 (imdb_id,
                                                  personal_rating,
                                                  self.user_name,
                                                  filmempf_id
                                                  )
            )
        self.conn.commit()
        
    
    def store_Imdb_MainAttributes_InDatabase(self, imdb_id, title, imdb_rater_count, release_year, runtime, imdb_rating):
        self.conn.execute('''INSERT OR REPLACE INTO Movie_imdbData (imdbID, 
                                                               Title_imdb, 
                                                               Rater_imdb, 
                                                               Release_imdb, 
                                                               Runtime_imdb, 
                                                               Rating_imdb
                                                               )
                                                               VALUES (?,?,?,?,?,?)''',           
                                                             (imdb_id, 
                                                              title, 
                                                              imdb_rater_count, 
                                                              release_year, 
                                                              runtime, 
                                                              imdb_rating
                                                              )
                        )
        self.conn.commit()
    
    
    def store_Imdb_Genres_InDatabase(self, imdb_id, genres):
        for genre in genres:
            self.conn.execute('''INSERT OR IGNORE INTO Movie_Genre (imdbID, 
                                                                    Genre_imdb 
                                                                    )
                                                                    VALUES (?,?)''',           
                                                                     (imdb_id,
                                                                      genre
                                                                      )
                        )
        self.conn.commit()
    
    
    def store_Imdb_Writer_InDatabase(self, imdb_id, writer):
        for write in writer:
            self.conn.execute('''INSERT OR IGNORE INTO Movie_Writer (imdbID, 
                                                                     Writer_imdb 
                                                                     )
                                                                     VALUES (?,?)''',           
                                                                    (imdb_id,
                                                                     write
                                                                     )
                             )
        self.conn.commit()
    
    
    def store_Imdb_Director_InDatabase(self, imdb_id, director):
        for direct in director:
            self.conn.execute('''INSERT OR IGNORE INTO Movie_Director(imdbID, 
                                                                 Director_imdb 
                                                                 )
                                                                 VALUES (?,?)''',           
                                                                 (imdb_id,
                                                                  direct
                                                                  )
                        )
        self.conn.commit()
    
    
    def store_Imdb_Country_InDatabase(self, imdb_id, country):
        for count in country:
            self.conn.execute('''INSERT OR IGNORE INTO Movie_Country(imdbID, 
                                                                Country_imdb 
                                                                )
                                                                VALUES (?,?)''',           
                                                                 (imdb_id,
                                                                  count
                                                                  )
                        )
        self.conn.commit()
    
    
    def store_Imdb_SimilarMovies_InDatabase(self, imdb_id, similar):
        for sim in similar:
            self.conn.execute('''INSERT OR REPLACE INTO Movie_Similar(imdbID, 
                                                                SimilarMovieID_imdb 
                                                                )
                                                                VALUES (?,?)''',           
                                                                 (imdb_id,
                                                                  sim
                                                                  )
                        )
        self.conn.commit()
    
    
    def store_Imdb_Cast_InDatabase(self, imdb_id, cast):
        for star in cast:
            self.conn.execute('''INSERT OR IGNORE INTO Movie_Star(imdbID, 
                                                                Star_imdb 
                                                                )
                                                                VALUES (?,?)''',           
                                                                 (imdb_id,
                                                                  star
                                                                  )
                        )
        self.conn.commit()
    
    
    def store_PotentialMovie_InDatabase(self, imdb_id, title, calculated_rating, user_name):
        print("Saving movie in database for potential new movies.")
        self.conn.execute('''INSERT OR REPLACE INTO Potential_Movies (imdbID, 
                                                          Title_imdb,
                                                          Calculated_Rating,
                                                          Rater
                                                          )
                                                          VALUES (?,?,?,?)''',           
                                                         (imdb_id, 
                                                          title,
                                                          calculated_rating,
                                                          user_name)
                            )
        self.conn.commit() 
    
    
    def getOwnRatedTopMovies(self):
        cursor = self.conn.execute('''SELECT imdbID FROM Own_Rating WHERE Rater = ? AND Personal_Rating >= 80 ORDER BY Personal_Rating DESC''', (self.user_name,))
        self.TopMovieList = []    
        for row in cursor:
            self.TopMovieList.append(row[0])
        return self.TopMovieList

        

    def get_allRatedMoviesIdList(self):
        self.rated_movies_list = []
        cursor = self.conn.execute(''' SELECT  imdbID FROM Own_Rating WHERE Rater = ? ''',(self.user_name,))
        for row in cursor:
            self.rated_movies_list.append(row[0])
        return self.rated_movies_list
    
    
    def get_allRatedMoviesDict(self):
        self.rated_movie_dict = {}
        cursor = self.conn.execute(''' SELECT  Movie_imdbData.imdbID, Title_imdb,Rater_imdb, Release_imdb, Runtime_imdb, Rating_imdb
                                       FROM Movie_imdbData
                                       LEFT JOIN Own_Rating
                                       ON Movie_imdbData.imdbID = Own_Rating.imdbID
                                       WHERE Rater = ? ''', (self.user_name,))
        for row in cursor:
            self.rated_movie_dict[row[0]] = {}
            self.rated_movie_dict[row[0]]["Title"] = row[1]
            self.rated_movie_dict[row[0]]["Rater_Count"] = row[2]
            self.rated_movie_dict[row[0]]["Release"] = row[3]
            self.rated_movie_dict[row[0]]["Runtime"] = row[4]
            self.rated_movie_dict[row[0]]["imdb_Rating"] = row[5]
        #Country Attributes
        cursor = self.conn.execute(''' SELECT  Movie_Country.imdbID, Country_imdb 
                                       FROM Movie_Country
                                       LEFT JOIN Own_Rating
                                       ON Movie_Country.imdbID = Own_Rating.imdbID
                                       WHERE Rater = ?''', (self.user_name,))
        for row in cursor: 
            self.rated_movie_dict[row[0]]["Country"] = self.rated_movie_dict[row[0]].get("Country",[]) + [row[1]]
        #Director Attributes
        cursor = self.conn.execute(''' SELECT  Movie_Director.imdbID, Director_imdb 
                                       FROM Movie_Director
                                       LEFT JOIN Own_Rating
                                       ON Movie_Director.imdbID = Own_Rating.imdbID
                                       WHERE Rater = ?''', (self.user_name,))
        for row in cursor: 
            self.rated_movie_dict[row[0]]["Director"] = self.rated_movie_dict[row[0]].get("Director",[]) + [row[1]]
        #Genre Attributes
        cursor = self.conn.execute(''' SELECT  Movie_Genre.imdbID, Genre_imdb 
                                       FROM Movie_Genre
                                       LEFT JOIN Own_Rating
                                       ON Movie_Genre.imdbID = Own_Rating.imdbID
                                       WHERE Rater = ?''', (self.user_name,))
        for row in cursor: 
            self.rated_movie_dict[row[0]]["Genre"] = self.rated_movie_dict[row[0]].get("Genre",[]) + [row[1]]
        #Similar Attributes
        cursor = self.conn.execute(''' SELECT  Movie_Similar.imdbID, SimilarMovieID_imdb
                                       FROM Movie_Similar
                                       LEFT JOIN Own_Rating
                                       ON Movie_Similar.imdbID = Own_Rating.imdbID
                                       WHERE Rater = ?''', (self.user_name,))
        for row in cursor: 
            self.rated_movie_dict[row[0]]["SimilarMovie"] = self.rated_movie_dict[row[0]].get("SimilarMovie",[]) + [row[1]]
        #Star List
        cursor = self.conn.execute(''' SELECT  Movie_Star.imdbID, Star_imdb
                                       FROM Movie_Star
                                       LEFT JOIN Own_Rating
                                       ON Movie_Star.imdbID = Own_Rating.imdbID
                                       WHERE Rater = ?''', (self.user_name,))
        for row in cursor: 
            self.rated_movie_dict[row[0]]["Star"] = self.rated_movie_dict[row[0]].get("Star",[]) + [row[1]]
        #Writer List
        cursor = self.conn.execute(''' SELECT  Movie_Writer.imdbID, Writer_imdb
                                       FROM Movie_Writer
                                       LEFT JOIN Own_Rating
                                       ON Movie_Writer.imdbID = Own_Rating.imdbID
                                       WHERE Rater = ?''', (self.user_name,))
        for row in cursor: 
            self.rated_movie_dict[row[0]]["Writer"] = self.rated_movie_dict[row[0]].get("Writer",[]) + [row[1]] 
        #Personal Rating
        cursor = self.conn.execute(''' SELECT  imdbID, Personal_Rating
                                       FROM Own_Rating
                                       WHERE Rater = ?''', (self.user_name,))
        for row in cursor: 
            self.rated_movie_dict[row[0]]["Personal_Rating"] = row[1]
        #Return final dict
        return self.rated_movie_dict
        

    def get_allPotentialMoviesList(self):
        self.potential_movies_list = []
        cursor = self.conn.execute(''' SELECT  imdbID FROM Potential_Movies WHERE Rater = ? ''',(self.user_name,))
        for row in cursor:
            self.potential_movies_list.append(row[0])
        return self.potential_movies_list
    
    
    def get_OrderedPotentialMovies(self,movie_count):
        cursor = self.conn.execute('''SELECT  imdbID,Title_imdb,Calculated_Rating FROM Potential_Movies WHERE Rater = ?  ORDER BY Calculated_Rating DESC LIMIT ?''',(self.user_name,movie_count))
        return cursor
        

    def get_similarMovieRatings(self, imdb_id):
        try:
            similars = self.rated_movie_dict[imdb_id]["SimilarMovie"]
        except KeyError:
            return ""
        ratings = []
        for movies in similars:
            try:
                ratings.append(self.rated_movie_dict[movies]["Personal_Rating"])
            except KeyError:
                continue
        return ratings       