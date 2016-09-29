# -*- coding: utf-8 -*-
"""
Created on Fri Sep  9 15:32:37 2016

@author: Tobi
"""


import re
import time
import Imdb_Scraper
import Filmempfehlung_Scraper
import Database_Handler
import Recommender_Engine



        
userid = ""
while userid != "break":   
    userid = input("Please enter your filmempfehlung.com id: " )
    user = Filmempfehlung_Scraper.FilmempfehlungUser(userid)
    user_descision = input("Is" , user.profil_name , "the rigth username? Write y/n: ")
    if user_descision == "y":
        break
user_database = Database_Handler.Database_Movies(user.profil_name)
user_recommender = Recommender_Engine.Recommender(user.profil_name)
while True:
    user_input = input("\nUse one of the following commands in the recommend mode:\n'ask' -  ask for the estimated rating for a specific movie.\n'search' -  start a automatic search for potential new movies to watch.\n'update' - calculate new ratings for your already recommended and stored movies.\n'show' - shows the movies in your potential new movie table with the highest estimated rating\n'break' - quit the recommendation mode\nYour input: ")
    if user_input == "show":
        show_input = input("Enter the number of movies you wish to see: " )
        print("\nCurrently the", show_input, "movies with the highest estimated rating in your database for potential new movies are:...\n")                         
        best_potential_movies = user_database.get_OrderedPotentialMovies(int(show_input))                    
        for row in best_potential_movies:
            print("imdbID:",row[0], row[1].strip() ,":", str(row[2])[:6])
    if user_input == "ask":
        while True:
            imdb_link = input("\nInsert imdb link (Example link: http://www.imdb.com/title/tt1014763/)\nWrite 'break' to quit the ask mode:....\nYour input:   " )
            if imdb_link == "break":
                break
            imdb_id = re.findall("title/tt(.+)/", imdb_link)
            imdb_id = int(imdb_id[0])
            try:
                single_movie_object = Imdb_Scraper.Imdb_Movie(imdb_id)
            except TypeError:
                print("\nNo proper imdb link! Please insert another link")
                continue
            ask_single_movie_dict = user_recommender.createSingleMovieTestData(single_movie_object)
            if "Similar_Movie_Average" in ask_single_movie_dict:
                user_recommender.askMovieRating_withSimilar(ask_single_movie_dict)
            else:
                user_recommender.askMovieRating_withoutSimilar(ask_single_movie_dict)
    if user_input == "search":
        while True:
            search_control = input("\nUse one of the following commands in the search mode:\n'random' - start a random imdb search for good movies.\n'similar' - search for good movies similar to your top rated movies.\n'break' - quit the search mode\nYour input: ")
            if search_control == "random":
                random_search_control = ""
                random_search_control_page = int(input("Insert starting page: "))
                search_engine = Imdb_Scraper.Imdb_RandomSearch(random_search_control_page)
                while random_search_control != "break":
                    search_engine.GenerateSearchUrl()
                    page_list = search_engine.getMovieListForSearchSite(user_database.rated_movie_dict)
                    print("\nScraping imdb search page", search_engine.search_page)
                    for movie in page_list:
                        singleSearch_movie = Imdb_Scraper.Imdb_Movie(movie)
                        single_movie_dict = user_recommender.createSingleMovieTestData(singleSearch_movie)
                        potential_movie_list = user_database.get_allPotentialMoviesList()
                        if single_movie_dict["id"] not in potential_movie_list and single_movie_dict["id"] not in user_database.rated_movies_list and "Similar_Movie_Average" in single_movie_dict:
                            movie_rating = user_recommender.predictMovieRating_Search(single_movie_dict)
                            if movie_rating >= 80:
                                search_engine.added_movies[single_movie_dict["Title"]] = movie_rating
                        time.sleep(3)
                    print("\nOverall",len(search_engine.added_movies),"new movies added to potential movie table")
                    random_search_control = input("Press Enter to continue the search. Write 'break' to quit.\nYour input: ")
                    search_engine.search_page = search_engine.search_page + 1
                print("\nSearch results. Following movies added to potential movies:...")
                for key in search_engine.added_movies:
                    print(key.strip(),":",str(search_engine.added_movies[key])[:6])
                print("\nCurrently the 20 movies with the highest estimated rating in your database for potential new movies are:...")
                best_potential_movies = user_database.get_OrderedPotentialMovies(20)
                print("\n")                            
                for row in best_potential_movies:
                    print("imdbID:",row[0], row[1].strip() ,":", str(row[2])[:6])
            if search_control == "similar":
                similar_search_control = ""
                while similar_search_control != "break":
                    search_results = {}
                    own_top_movies = user_database.getOwnRatedTopMovies()
                    for imdbid in own_top_movies:
                        top_movie = Imdb_Scraper.Imdb_Movie(imdbid)
                        print("Similar Movies to:",top_movie.title)
                        for similar in top_movie.similars:
                            potential_movies = user_database.get_allPotentialMoviesList()
                            if similar in user_database.rated_movies_list or similar in potential_movies:
                                continue
                            time.sleep(5)
                            similarSearch_movie = Imdb_Scraper.Imdb_Movie(similar)
                            single_movie_dict = user_recommender.createSingleMovieTestData(similarSearch_movie)
                            if "Similar_Movie_Average" in single_movie_dict:
                                movie_rating = user_recommender.predictMovieRating_Search(single_movie_dict)
                                if movie_rating >= 80:
                                    search_results[single_movie_dict["Title"]] = movie_rating
                        print("\nOverall",len(search_results),"new movies added to potential movie table")
                        similar_search_control = input("\nWrite 'break' to quit the similar search.\nPress Enter to continue.")
                        if similar_search_control == "break":
                            break
                print("\nSearch results. Following movies added to potential movies:...")
                for key in search_results:
                    print(key.strip(),":",str(search_results[key])[:6])
                print("\nCurrently the 20 movies with the highest estimated rating in your database for potential new movies are:...")
                best_potential_movies = user_database.get_OrderedPotentialMovies(20)
                print("\n")                            
                for row in best_potential_movies:
                    print("imdbID:",row[0], row[1].strip() ,":", str(row[2])[:6])
            if search_control == "break":
                break
    if user_input == "break":
        break
