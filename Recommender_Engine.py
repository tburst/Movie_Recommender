# -*- coding: utf-8 -*-
"""
Created on Thu Sep 29 16:03:20 2016

@author: Tobi
"""


import sqlite3
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import Database_Handler
        




class Recommender:
    

    def __init__(self, user_name):
        self.user_name = user_name
        self.rated_movie_dict = Database_Handler.Database_Movies(user_name).get_allRatedMoviesDict()
        self.conn = sqlite3.connect('Movie_Database.db')
        self.determineRelevantCountryFeatures()
        self.determineRelevantDirectorFeatures()
        self.determineRelevantGenreFeatures()
        self.determineRelevantStarFeatures()
        self.determineRelevantWriterFeatures()
        self.create_PandaTrainingDataframe()
        self.get_FeatureNamesWithSimilar()
        self.get_FeatureNamesWithoutSimilar()
        print("Building main model with similar movie ratings")
        self.ModelWithSimilar = self.trainModel(self.trainingFeatures_withSimilar)
        print("Building backup model without similar movie ratings")
        self.ModelWithoutSimilar = self.trainModel(self.trainingFeatures_withoutSimilar)


    def determineRelevantCountryFeatures(self):
        cursor = self.conn.execute( '''SELECT Country_imdb, COUNT(Country_imdb) AS Country_Count
                                       FROM Movie_Country
                                       LEFT JOIN Own_Rating
                                       ON Movie_Country.imdbID = Own_Rating.imdbID
                                       WHERE Rater = ?
                                       GROUP BY Country_imdb
                                       ORDER BY Country_Count DESC''' , (self.user_name,))
        self.relevant_Countries = []
        for row in cursor:
            if row[1] < 20:
                break
            self.relevant_Countries.append(row[0])
        return self.relevant_Countries



    def determineRelevantWriterFeatures(self):
        cursor = self.conn.execute( '''SELECT Writer_imdb, COUNT(Writer_imdb) AS Writer_Count
                                       FROM Movie_Writer
                                       LEFT JOIN Own_Rating
                                       ON Movie_Writer.imdbID = Own_Rating.imdbID
                                       WHERE Rater = ?
                                       GROUP BY Writer_imdb
                                       ORDER BY Writer_Count DESC''' , (self.user_name,))
        self.relevant_Writer = []
        for row in cursor:
            if row[1] < 6:
                break
            self.relevant_Writer.append(row[0])
        return self.relevant_Writer


    def determineRelevantGenreFeatures(self):
        cursor = self.conn.execute( '''SELECT Genre_imdb, COUNT(Genre_imdb) AS Genre_Count
                                       FROM Movie_Genre
                                       LEFT JOIN Own_Rating
                                       ON Movie_Genre.imdbID = Own_Rating.imdbID
                                       WHERE Rater = ?
                                       GROUP BY Genre_imdb
                                       ORDER BY Genre_Count DESC''' , (self.user_name,))
        self.relevant_Genre = []
        for row in cursor:
            if row[1] < 10:
                break
            self.relevant_Genre.append(row[0])
        return self.relevant_Genre


    def determineRelevantStarFeatures(self):
        cursor = self.conn.execute( '''SELECT Star_imdb, COUNT(Star_imdb) AS Star_Count
                                       FROM Movie_Star
                                       LEFT JOIN Own_Rating
                                       ON Movie_Star.imdbID = Own_Rating.imdbID
                                       WHERE Rater = ?
                                       GROUP BY Star_imdb
                                       ORDER BY Star_Count DESC''' , (self.user_name,))
        self.relevant_Stars = []
        for row in cursor:
            if row[1] < 15:
                break
            self.relevant_Stars.append(row[0])
        return self.relevant_Stars


    def determineRelevantDirectorFeatures(self):
        cursor = self.conn.execute( '''SELECT Director_imdb, COUNT(Director_imdb) AS Director_Count
                                       FROM Movie_Director
                                       LEFT JOIN Own_Rating
                                       ON Movie_Director.imdbID = Own_Rating.imdbID
                                       WHERE Rater = ?
                                       GROUP BY Director_imdb
                                       ORDER BY Director_Count DESC''' , (self.user_name,))
        self.relevant_Directors = []
        for row in cursor:
            if row[1] < 8:
                break
            self.relevant_Directors.append(row[0])
        return self.relevant_Directors
                
                
    def check_OscarWinnerMale(self, cast):
        Oscar_Winner_Male = ["Eddie Redmayne","Matthew McConaughey",
                             "Daniel Day-Lewis","Jean Dujardin",
                             "Colin Firth","Jeff Bridges",
                             "Sean Penn","Forest Whitaker",
                             "Philip Seymour Hoffman","Jamie Foxx",
                             "Adrien Brody","Denzel Washington",
                             "Russell Crowe","Kevin Spacey",
                             "Roberto Benigni","Jack Nicholson",
                             "Geoffrey Rush","Nicolas Cage",
                             "Tom Hanks","Al Pacino",
                             "Anthony Hopkins","Jeremy Irons",
                             "Dustin Hoffman", "Michael Douglas"
                             "Paul Newman","William Hurt"
                             "Robert Duvall","Ben Kingsley",
                             "Henry Fonda","Robert De Niro",
                             ]
        OscarWinnerMaleInCast = False
        while True:
            try:
                for values in cast:
                    if values in Oscar_Winner_Male:
                        OscarWinnerMaleInCast = True
                        return OscarWinnerMaleInCast
                return OscarWinnerMaleInCast
                break
            except KeyError:
                return OscarWinnerMaleInCast
                break


    def check_OscarWinnerFemale(self, cast):
        Oscar_Winner_Female = ["Julianne Moore","Cate Blanchett",
                             "Jennifer Lawrence","Meryl Streep",
                             "Natalie Portman", "Sandra Bullock",
                             "Kate Winslet", "Marion Cotillard",
                             "Helen Mirren", "Reese Witherspoon",
                             "Hilary Swank", "Charlize Theron",
                             "Nicole Kidman", "Halle Berry",
                             "Julia Roberts", "Helen Hunt",
                             "Gwyneth Paltrow", "Frances McDormand",
                             "Susan Sarandon", "Jessica Lange",
                             "Holly Hunter", "Emma Thompson",
                             "Jodie Foster", "Kathy Bates",
                             "Jessica Tandy", "Cher",
                             "Marlee Matlin", "Geraldine Page",
                             "Sally Field", "Shirley MacLaine",
                             "Katharine Hepburn", "Sissy Spacek",
                             ]
        OscarWinnerFemaleInCast = False
        while True:
            try:
                for values in cast:
                    if values in Oscar_Winner_Female:
                        OscarWinnerFemaleInCast = True
                        return OscarWinnerFemaleInCast
                return OscarWinnerFemaleInCast
                break
            except KeyError:
                return OscarWinnerFemaleInCast
                break
      
            
    def get_similarRatingTrain(self, imdb_id):
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
        return np.mean(ratings)   


    def get_similarRatingTest(self, singleMovie_object):
        similar_ratings = []
        similars = singleMovie_object.similars
        for similar_movie in similars:
            cursor = self.conn.execute(''' SELECT  Personal_Rating FROM Own_Rating WHERE imdbID == ? AND Rater == ? ''', (similar_movie,self.user_name))
            rating = cursor.fetchone()
            try:
                similar_ratings.append(rating[0])
            except TypeError:
                continue   
        return similar_ratings
            

    def create_PandaTrainingDataframe(self):
        self.movie_pandas_list = []
        for row in self.rated_movie_dict.keys():
            movie = self.rated_movie_dict.get(row,{})
            single_movie_dict = {"id": row,"Title": movie["Title"],"Rater_Count":movie["Rater_Count"],
                                 "imdb_Rating": movie["imdb_Rating"],"Personal_Rating":movie["Personal_Rating"],
                                 "Release": movie["Release"],"Runtime": movie["Runtime"]}
            for country in self.relevant_Countries:
                single_movie_dict["Country_"+country] = country in movie["Country"]
            for writer in self.relevant_Writer:
                try:
                    single_movie_dict["Writer_"+writer] = writer in movie["Writer"]
                except KeyError:
                    single_movie_dict["Writer_"+writer] = False
            for genre in self.relevant_Genre:
                try:
                    single_movie_dict["Genre_"+genre] = genre in movie["Genre"]
                except KeyError:
                    single_movie_dict["Genre_"+genre] = False
            for star in self.relevant_Stars:
                try:
                    single_movie_dict["Star_"+star] = writer in movie["Star"]
                except KeyError:
                    single_movie_dict["Star_"+star] = False
            for director in self.relevant_Directors:
                try:
                    single_movie_dict["Director_"+director] = writer in movie["Director"]
                except KeyError:
                    single_movie_dict["Director_"+director] = False
            single_movie_dict["OscarWinnerMale_Since1980"] = self.check_OscarWinnerMale(movie.get("Star",[]))
            single_movie_dict["OscarWinnerFemale_Since1980"] = self.check_OscarWinnerFemale(movie.get("Star",[]))
            single_movie_dict["Similar_Movie_Average"] = self.get_similarRatingTrain(row)
            self.movie_pandas_list.append(single_movie_dict)
        self.trainingData = pd.DataFrame(self.movie_pandas_list)
        self.trainingData[["Runtime","Similar_Movie_Average"]] = self.trainingData[["Runtime","Similar_Movie_Average"]].apply(pd.to_numeric)
        self.trainingData  = self.trainingData.dropna()
        return self.trainingData


    def get_FeatureNamesWithSimilar(self):
        self.trainingFeatures_withSimilar = ["Release","imdb_Rating","Runtime","Rater_Count","OscarWinnerMale_Since1980",
                            "OscarWinnerFemale_Since1980", "Similar_Movie_Average"]
        for country in self.relevant_Countries:
            self.trainingFeatures_withSimilar.append("Country_" + country)
        for writer in self.relevant_Writer:
            self.trainingFeatures_withSimilar.append("Writer_" + writer)
        for genre in self.relevant_Genre:
            self.trainingFeatures_withSimilar.append("Genre_" + genre)
        for star in self.relevant_Stars:
            self.trainingFeatures_withSimilar.append("Star_" + star)
        for director in self.relevant_Directors:
            self.trainingFeatures_withSimilar.append("Director_" + director)
        return self.trainingFeatures_withSimilar     
        
        
    def get_FeatureNamesWithoutSimilar(self):
        self.trainingFeatures_withoutSimilar = ["Release","imdb_Rating","Runtime","Rater_Count","OscarWinnerMale_Since1980",
                            "OscarWinnerFemale_Since1980"]
        for country in self.relevant_Countries:
            self.trainingFeatures_withoutSimilar.append("Country_" + country)
        for writer in self.relevant_Writer:
            self.trainingFeatures_withoutSimilar.append("Writer_" + writer)
        for genre in self.relevant_Genre:
            self.trainingFeatures_withoutSimilar.append("Genre_" + genre)
        for star in self.relevant_Stars:
            self.trainingFeatures_withoutSimilar.append("Star_" + star)
        for director in self.relevant_Directors:
            self.trainingFeatures_withoutSimilar.append("Director_" + director)
        return self.trainingFeatures_withoutSimilar 


    def trainModel(self, trainingFeatures):
        predictors= self.trainingData[trainingFeatures] 
        targets = self.trainingData["Personal_Rating"].values
        print("There are overall",len(self.trainingData.index),"movies with", len(trainingFeatures),"features to train the algorithm")     
        print("Training random forest model...")
        forest = RandomForestRegressor(n_estimators = 3000, max_features = int(len(trainingFeatures)/3))
        forest = forest.fit(predictors,targets)
        return forest

    def createSingleMovieTestData(self, singleMovie_object):
        self.singleMovie_object = singleMovie_object
        single_movie_dict_testdata = {}
        single_movie_dict_testdata["id"] = self.singleMovie_object.imdb_id
        single_movie_dict_testdata["Title"] = self.singleMovie_object.title
        single_movie_dict_testdata["Rater_Count"] = self.singleMovie_object.rater
        single_movie_dict_testdata["Release"] = self.singleMovie_object.year
        single_movie_dict_testdata["Runtime"] = self.singleMovie_object.runtime
        single_movie_dict_testdata["imdb_Rating"]  = self.singleMovie_object.rating
        for country in self.relevant_Countries:
            single_movie_dict_testdata["Country_"+country] = country in self.singleMovie_object.country
        for writer in self.relevant_Writer:
            try:
                single_movie_dict_testdata["Writer_"+writer] = writer in self.singleMovie_object.writer
            except KeyError:
                single_movie_dict_testdata["Writer_"+writer] = False
        for genre in self.relevant_Genre:
            single_movie_dict_testdata["Genre_"+genre] = genre in self.singleMovie_object.genres 
        for star in self.relevant_Stars:
            try:
                single_movie_dict_testdata["Star_"+star] = writer in self.singleMovie_object.cast
            except KeyError:
                single_movie_dict_testdata["Star_"+star] = False
        for director in self.relevant_Directors:
            try:
                single_movie_dict_testdata["Director_"+director] = writer in self.singleMovie_object.director
            except KeyError:
                single_movie_dict_testdata["Director_"+director] = False
        similar_ratings = self.get_similarRatingTest(self.singleMovie_object)
        if not similar_ratings:
            single_movie_dict_testdata["OscarWinnerMale_Since1980"] = self.check_OscarWinnerMale(self.singleMovie_object.cast)
            single_movie_dict_testdata["OscarWinnerFemale_Since1980"] = self.check_OscarWinnerFemale(self.singleMovie_object.cast)
        else:
            similar_ratings = np.mean(similar_ratings)
            single_movie_dict_testdata["Similar_Movie_Average"] =  similar_ratings
            single_movie_dict_testdata["OscarWinnerMale_Since1980"] = self.check_OscarWinnerMale(self.singleMovie_object.cast)
            single_movie_dict_testdata["OscarWinnerFemale_Since1980"] = self.check_OscarWinnerFemale(self.singleMovie_object.cast)
        return single_movie_dict_testdata
    
    
    def createSinglePredictors(self, single_movie_dict_testdata):
        testData = pd.DataFrame([single_movie_dict_testdata])
        if "Similar_Movie_Average" not in single_movie_dict_testdata:
            new_movie_data_predictors = testData[self.trainingFeatures_withoutSimilar]
        else:
            new_movie_data_predictors = testData[self.trainingFeatures_withSimilar]
        return new_movie_data_predictors
    
    
    def askMovieRating_withSimilar(self, single_movie_dict_testdata):
        User_Movies = Database_Handler.Database_Movies(self.user_name)
        watched_movie_list = User_Movies.get_allRatedMoviesIdList()
        if single_movie_dict_testdata["id"] not in watched_movie_list:
            if not self.singleMovie_object.is_series:
                if self.singleMovie_object.rating >= 0 and self.singleMovie_object.rater >= 0:
                    new_movie_data_predictors = self.createSinglePredictors(single_movie_dict_testdata)
                    calculated_rating = self.ModelWithSimilar.predict(new_movie_data_predictors)
                    print("\nEnough similar movies in your personal database. Using main model")
                    print("\nYou would rate the movie ", self.singleMovie_object.title.strip(), " with a rating of: ",calculated_rating[0] )
                    if calculated_rating >= 80:
                        User_Movies.store_Imdb_MainAttributes_InDatabase(self.singleMovie_object.imdb_id, self.singleMovie_object.title, self.singleMovie_object.rater, self.singleMovie_object.year, self.singleMovie_object.runtime, self.singleMovie_object.rating)
                        User_Movies.store_Imdb_Genres_InDatabase(self.singleMovie_object.imdb_id, self.singleMovie_object.genres)
                        User_Movies.store_Imdb_Writer_InDatabase(self.singleMovie_object.imdb_id, self.singleMovie_object.writer)
                        User_Movies.store_Imdb_Director_InDatabase(self.singleMovie_object.imdb_id, self.singleMovie_object.director)
                        User_Movies.store_Imdb_Country_InDatabase(self.singleMovie_object.imdb_id, self.singleMovie_object.country)
                        User_Movies.store_Imdb_SimilarMovies_InDatabase(self.singleMovie_object.imdb_id, self.singleMovie_object.similars)
                        User_Movies.store_Imdb_Cast_InDatabase(self.singleMovie_object.imdb_id, self.singleMovie_object.cast)
                        User_Movies.store_PotentialMovie_InDatabase(self.singleMovie_object.imdb_id, self.singleMovie_object.title, calculated_rating[0], self.user_name)
                else:
                    print("\nMovie has no imdb Rating")
            else:
                print("\nSeries are currently not supported!")
        else:
            print("\n Movie already watched!")
                
                
    def askMovieRating_withoutSimilar(self, single_movie_dict_testdata):  
        User_Movies = Database_Handler.Database_Movies(self.user_name)
        watched_movie_list = User_Movies.get_allRatedMoviesIdList()
        if single_movie_dict_testdata["id"] not in watched_movie_list:
            if not self.singleMovie_object.is_series:
                if self.singleMovie_object.rating >= 0 and self.singleMovie_object.rater >= 0:
                    new_movie_data_predictors = self.createSinglePredictors(single_movie_dict_testdata)
                    calculated_rating = self.ModelWithoutSimilar.predict(new_movie_data_predictors)
                    print("\nNot enough similar movies in your personal database. Using weaker backup model")
                    print("\nYou would rate the movie ", self.singleMovie_object.title.strip(), " with a rating of: ",calculated_rating[0] )
                else:
                    print("\nMovie has no imdb Rating")
            else:
                print("\nSeries are currently not supported!")
        else:
            print("\n Movie already watched!")
    
    
    def predictMovieRating_Search(self, single_movie_dict_testdata):
        User_Movies = Database_Handler.Database_Movies(self.user_name)
        if not self.singleMovie_object.is_series:
            if self.singleMovie_object.rating >= 0 and self.singleMovie_object.rater >= 0:
                new_movie_data_predictors = self.createSinglePredictors(single_movie_dict_testdata)
                calculated_rating = self.ModelWithSimilar.predict(new_movie_data_predictors)
                print("\nMovie:", "'" + self.singleMovie_object.title.strip() + "'", " calculated Rating: ",calculated_rating[0] )
                if calculated_rating[0] >= 80:
                    User_Movies.store_Imdb_MainAttributes_InDatabase(self.singleMovie_object.imdb_id, self.singleMovie_object.title, self.singleMovie_object.rater, self.singleMovie_object.year, self.singleMovie_object.runtime, self.singleMovie_object.rating)
                    User_Movies.store_Imdb_Genres_InDatabase(self.singleMovie_object.imdb_id, self.singleMovie_object.genres)
                    User_Movies.store_Imdb_Writer_InDatabase(self.singleMovie_object.imdb_id, self.singleMovie_object.writer)
                    User_Movies.store_Imdb_Director_InDatabase(self.singleMovie_object.imdb_id, self.singleMovie_object.director)
                    User_Movies.store_Imdb_Country_InDatabase(self.singleMovie_object.imdb_id, self.singleMovie_object.country)
                    User_Movies.store_Imdb_SimilarMovies_InDatabase(self.singleMovie_object.imdb_id, self.singleMovie_object.similars)
                    User_Movies.store_Imdb_Cast_InDatabase(self.singleMovie_object.imdb_id, self.singleMovie_object.cast)
                    User_Movies.store_PotentialMovie_InDatabase(self.singleMovie_object.imdb_id, self.singleMovie_object.title, calculated_rating[0], self.user_name)
                return calculated_rating[0]
        else:
            return -1