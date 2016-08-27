# -*- coding: utf-8 -*-

import time
import re
import datetime
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import sqlite3
import numpy as np
from bs4 import BeautifulSoup
import urllib.request
import random



#Defining functions to scrape imdb data

def get_rating(soup):
    tags = soup("span", itemprop="ratingValue")
    for tag in tags:
        rating = float(tag.contents[0])
    return rating


def get_title(soup): 
    title = soup.find(attrs={"itemprop" : "name"})
    [s.extract() for s in title('span')]
    title = title.text
    return title


def get_rater(soup):
    tags = str(soup("span", itemprop="ratingValue"))
    rater = re.findall("<strong title=.+?(\d+,\d+)", tags)
    if rater == []:
        rater = re.findall("<strong title=.+?(\d+)", tags)
    if rater == []:
        tags = str(soup("span", itemprop="ratingCount"))
        rater = re.findall('ratingCount">(\d+,\d+)', tags)
    if rater == []:
        rater = re.findall('ratingCount">(\d+)', tags)   
    rater = int(rater[0].replace(",",""))
    return rater


def get_year(soup):
    tags = soup.find("div", {"class": "subtext"})
    tags = tags.find("meta",attrs={"itemprop" : "datePublished"})["content"]
    if "-" in tags:
        try:
            year = datetime.datetime.strptime(tags,"%Y-%m-%d")
            year = year.year
        except ValueError:
            year = datetime.datetime.strptime(tags,"%Y-%m")
            year = year.year    
    else:
        year = tags
    return int(year)
 
     
def get_runtime(soup):
    tags= soup("time", itemprop = "duration")
    i = 0
    runtime = None
    for tag in tags:
        runtime = str(tag.contents[0])
        i += 1
        if i == 2:
            break
    if runtime == None:
        runtime = ""
    elif "h" in runtime:
        hour = int(runtime[:runtime.find("h")])
        if runtime.find("m") == -1:
            minute = 0
        else:
            minute = int(runtime[runtime.find("h")+2:runtime.find("m")])
        runtime = hour * 60 + minute
    else:
        runtime = int(runtime.replace(" min",""))
    return runtime    

       
def get_genres(soup):
    tags= soup("span", itemprop = "genre")
    genres = []
    for tag in tags:
        genres.append(str(tag.contents[0]))
    return genres


def get_writer(soup):
    tags= str(soup("span", itemprop ="creator"))
    writer = re.findall('Person">\n.+itemprop="name">(.+?)</span', tags)
    return writer

       
def get_director(soup):
    tags= str(soup("span", itemprop ="director"))
    director = re.findall('itemprop="name">(.+?)</span', tags)  
    return director


def get_country(soup):
    tags= str(soup("div", { "class" : "txt-block" }))
    country= re.findall("country/.+itemprop=.url.>(.+)</a>", tags)
    return country


def get_similar(soup):
    tags= soup.findAll("div", { "class" : "rec_item" })
    similars = []
    for i in tags:
        y = i['data-tconst']
        y = int(re.sub("tt","",y))
        similars.append(y)
    return similars


def get_cast(soup):
    tags= str(soup("table", { "class" : "cast_list" }))
    cast= re.findall('title="(.+?)"', tags)
    return cast
    

def is_series(soup):
    tags = soup.find("meta",{"name":"title"})["content"]
    return "Series" in tags or "series" in tags
    

#Defining two functions to determine if a Oscar-Winner is among the cast members using a predefined list
    
def check_OscarWinnerMale(cast):
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
    try:
        for values in cast:
            if values in Oscar_Winner_Male:
                return True
        return False
    except KeyError:
        return False


def check_OscarWinnerFemale(cast):
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
    try:
        for values in cast:
            if values in Oscar_Winner_Female:
                return True
        return False
    except KeyError:
        return False


def get_similarRating(movie_dict, imdb_id):
    try:
        similars = movie_dict[imdb_id]["SimilarMovie"]
    except KeyError:
        return ""
    ratings = []
    for movies in similars:
        try:
            ratings.append(movie_dict[movies]["Personal_Rating"])
        except KeyError:
            continue
    return np.mean(ratings)


def determineCountryVariables(profilName):
    conn = sqlite3.connect('Movie_Database.db')
    cursor = conn.execute( '''SELECT Country_imdb, COUNT(Country_imdb) AS Country_Count
                              FROM Movie_Country
                              LEFT JOIN Own_Rating
                              ON Movie_Country.imdbID = Own_Rating.imdbID
                              WHERE Rater = ?
                              GROUP BY Country_imdb
                              ORDER BY Country_Count DESC''' , (profilName,))
    relevant_Countries = []
    for row in cursor:
        if row[1] < 20:
            break
        relevant_Countries.append(row[0])
    return relevant_Countries



def determineWriterVariables(profilName):
    conn = sqlite3.connect('Movie_Database.db')
    cursor = conn.execute( '''SELECT Writer_imdb, COUNT(Writer_imdb) AS Writer_Count
                              FROM Movie_Writer
                              LEFT JOIN Own_Rating
                              ON Movie_Writer.imdbID = Own_Rating.imdbID
                              WHERE Rater = ?
                              GROUP BY Writer_imdb
                              ORDER BY Writer_Count DESC''' , (profilName,))
    relevant_Writer = []
    for row in cursor:
        if row[1] < 6:
            break
        relevant_Writer.append(row[0])
    return relevant_Writer


def determineGenreVariables(profilName):
    conn = sqlite3.connect('Movie_Database.db')
    cursor = conn.execute( '''SELECT Genre_imdb, COUNT(Genre_imdb) AS Genre_Count
                              FROM Movie_Genre
                              LEFT JOIN Own_Rating
                              ON Movie_Genre.imdbID = Own_Rating.imdbID
                              WHERE Rater = ?
                              GROUP BY Genre_imdb
                              ORDER BY Genre_Count DESC''' , (profilName,))
    relevant_Genre = []
    for row in cursor:
        if row[1] < 10:
            break
        relevant_Genre.append(row[0])
    return relevant_Genre


def determineStarVariables(profilName):
    conn = sqlite3.connect('Movie_Database.db')
    cursor = conn.execute( '''SELECT Star_imdb, COUNT(Star_imdb) AS Star_Count
                              FROM Movie_Star
                              LEFT JOIN Own_Rating
                              ON Movie_Star.imdbID = Own_Rating.imdbID
                              WHERE Rater = ?
                              GROUP BY Star_imdb
                              ORDER BY Star_Count DESC''' , (profilName,))
    relevant_Stars = []
    for row in cursor:
        if row[1] < 15:
            break
        relevant_Stars.append(row[0])
    return relevant_Stars


def determineDirectorVariables(profilName):
    conn = sqlite3.connect('Movie_Database.db')
    cursor = conn.execute( '''SELECT Director_imdb, COUNT(Director_imdb) AS Director_Count
                              FROM Movie_Director
                              LEFT JOIN Own_Rating
                              ON Movie_Director.imdbID = Own_Rating.imdbID
                              WHERE Rater = ?
                              GROUP BY Director_imdb
                              ORDER BY Director_Count DESC''' , (profilName,))
    relevant_Directors = []
    for row in cursor:
        if row[1] < 8:
            break
        relevant_Directors.append(row[0])
    return relevant_Directors
    
    
        
#Functions to work with filmempfehlung.com data. 
        
#Takes desired page of movie site(default start is  page 1) and returns personal
#rating, imdb link and filmempfehlungs-id as dict

def get_ownMovieList(profil_id,page_site=1):
    service_url = "http://www.filmempfehlung.com/"
    page_site = str(page_site)
    link = service_url + "profil,"+profil_id+"_bewertungen~" + page_site + ".html"
    html = urllib.request.urlopen(link).read()
    soup = BeautifulSoup(html,"lxml")
    movie_dict = {}
    for movie in  soup.find_all("div",{"class": "float_left tc bewcov"}):
        rating = movie.find("div", {"class": "tc mt10 mb0"}).text
        rating = re.sub("%","",rating)
        rating = int(rating)
        movie_tags = movie.find("a")
        link = movie_tags["href"]
        link = service_url + link
        own_id = re.findall('filme,(\d+)\.',link)
        own_id = int(own_id[0])
        movie_dict[own_id] = {}
        movie_dict[own_id]["Rating"] = rating
        movie_dict[own_id]["Link"] = link
    return movie_dict
    

#Takes Filmempfehlungs_MovieLink and returns imdb link

def get_imdbLink(link):
    html = urllib.request.urlopen(link).read()
    soup = BeautifulSoup(html,'html.parser')
    imdb = soup.find("a",{"class" : "imdb"})
    imdb_link = imdb["href"]
    return imdb_link


#Takes id of filmempfehlung profil site and returns last page number     

def get_highestPage(profil_id):
    link = "http://www.filmempfehlung.com/profil," + profil_id + "_bewertungen~1.html"
    html = urllib.request.urlopen(link).read()
    soup = BeautifulSoup(html,'html.parser')
    tag = soup.find("div", {"class" : "seitennavi"})
    tag = tag.findAll("a", {"class" : "seiten1"})
    pages = []
    for i in tag:
        if i.text.isdigit():
            pages.append(int(i.text))
    pages = sorted(pages, reverse = True)
    return pages[0]  
    

#Takes id of filmempfehlung profil site and returns profil name
   
def get_profilName(profil_id):
    profil_id = str(profil_id)
    link = "http://www.filmempfehlung.com/profil," + profil_id + "_bewertungen~1.html"
    html = urllib.request.urlopen(link).read()
    soup = BeautifulSoup(html,'html.parser')
    tag = soup.find("div", {"class": "userbild"})
    tag = tag.find("a")
    profil_name = tag["title"]
    return profil_name
    

    

#First main Function: working with SQLite Database. Asks for filmempfehlung.com profil_id,
#scrapes movie data for every new movie and automatically stops if a movie is already stored in the database. 
#Creates Tables if they dont already exist

def filmempfToSQL(profil_id):
    last_page = get_highestPage(profil_id)
    profilName = get_profilName(profil_id)
    conn = sqlite3.connect('Movie_Database.db')
    #Create Tables if not already in database
    conn.execute(''' CREATE TABLE IF NOT EXISTS Movie_Country (imdbID NUMERIC,
                                                               Country_imdb VARCHAR(30),
                                                               PRIMARY KEY (imdbID, Country_imdb))  ''')
    conn.execute(''' CREATE TABLE IF NOT EXISTS Movie_Director (imdbID NUMERIC,
                                                                Director_imdb VARCHAR(30),
                                                        		  PRIMARY KEY (imdbID, Director_imdb))''')
    conn.execute(''' CREATE TABLE IF NOT EXISTS Movie_Genre (imdbID NUMERIC,
                                                             Genre_imdb VARCHAR(30),
                                                             PRIMARY KEY (imdbID, Genre_imdb))''')
    conn.execute(''' CREATE TABLE IF NOT EXISTS Movie_Similar(imdbID NUMERIC,
                                                              SimilarMovieID_imdb NUMERIC,
                                                              PRIMARY KEY (imdbID, SimilarMovieID_imdb ))''')
    conn.execute(''' CREATE TABLE IF NOT EXISTS Movie_Star(imdbID NUMERIC,
                                                           Star_imdb VARCHAR(30),
                                                           PRIMARY KEY (imdbID, Star_imdb))''')
    conn.execute(''' CREATE TABLE IF NOT EXISTS Movie_Writer(imdbID NUMERIC,
                                                             Writer_imdb VARCHAR(30),
                                                             PRIMARY KEY (imdbID, Writer_imdb))''')
    conn.execute('''CREATE TABLE IF NOT EXISTS Movie_imdbData(imdbID NUMERIC PRIMARY KEY,
                                                              Title_imdb VARCHAR(30),
                                                              Rater_imdb NUMERIC,
                                                              Release_imdb NUMERIC,
                                                              Runtime_imdb NUMERIC,
                                                              Rating_imdb Numeric)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS Own_Rating (imdbID NUMERIC,
                                                           Personal_Rating NUMERIC,
                                                           Rater VARCHAR(30), 
                                                           FilmempfehlungID NUMERIC,
                                                           PRIMARY KEY (imdbID, Rater  ))''')
    conn.execute('''CREATE TABLE IF NOT EXISTS Potential_Movies(imdbID NUMERIC,
                                                                Title_imdb VARCHAR(30),
                                                                Calculated_Rating NUMERIC,
                                                                Rater VARCHAR(30),
                                                                PRIMARY KEY (imdbID,Rater))''')
    #Get all movies already saved in database
    cursor = conn.execute(''' SELECT  imdbID FROM Own_Rating WHERE Rater = ? ''',(profilName,))
    rated_movies = []
    for row in cursor:
        rated_movies.append(row[0])
    #Loop over all profil pages to store movies in database
    for i in range(1, last_page + 1):
        print("Filmempfehlung.com Profil Page:",i)
        time.sleep(5)
        personal_movie_dict = get_ownMovieList(profil_id,i)
        break_after_page = False
        for movie in personal_movie_dict.keys():
            time.sleep(5)
            personal_rating = personal_movie_dict[movie]["Rating"]
            imdb_link = personal_movie_dict[movie]["Link"]
            imdb_link = get_imdbLink(imdb_link)
            if not imdb_link:
                print("No imdb Link for Movie with id:", movie)
                continue
            html = urllib.request.urlopen(imdb_link).read()
            soup = BeautifulSoup(html,"lxml")
            if is_series(soup):
                print("---skip Series!!!")
                continue
            imdb_id = re.findall("title/tt(.+)", imdb_link)
            imdb_id = int(imdb_id[0])
            #Exit loop if current movie already in database
            title = get_title(soup)
            if imdb_id in rated_movies:
                print("Movie " + "'" + title.strip() + "'" + " already in database!")
                break_after_page = True
                continue
            rater = profilName
            conn.execute('''DELETE FROM Potential_Movies WHERE imdbID = ?''',(imdb_id,)) 
            #Insert data for scraped movie in SQL-Database
            conn.execute('''INSERT OR REPLACE INTO Own_Rating (imdbID, 
                                                              Personal_Rating,
                                                              Rater,
                                                              FilmempfehlungID
                                                              )
                                                              VALUES (?,?,?,?)''',           
                                                             (imdb_id,
                                                              personal_rating,
                                                              rater,
                                                              movie
                                                              )
                        )
            imdb_rating = get_rating(soup)
            title = get_title(soup)
            print("'" + title.strip() + "'" + " added to database")
            imdb_rater_count = get_rater(soup)
            release_year = get_year(soup)
            runtime = get_runtime(soup)
            conn.execute('''INSERT OR REPLACE INTO Movie_imdbData (imdbID, 
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
            genres = get_genres(soup)
            for genre in genres:
                conn.execute('''INSERT OR IGNORE INTO Movie_Genre   (imdbID, 
                                                                     Genre_imdb 
                                                                     )
                                                                     VALUES (?,?)''',           
                                                                     (imdb_id,
                                                                      genre
                                                                      )
                            )
            writer = get_writer(soup)
            for write in writer:
                conn.execute('''INSERT OR IGNORE INTO Movie_Writer (imdbID, 
                                                                    Writer_imdb 
                                                                    )
                                                                    VALUES (?,?)''',           
                                                                    (imdb_id,
                                                                     write
                                                                     )
                            )
            director = get_director(soup)
            for direct in director:
                conn.execute('''INSERT OR IGNORE INTO Movie_Director(imdbID, 
                                                                     Director_imdb 
                                                                     )
                                                                     VALUES (?,?)''',           
                                                                     (imdb_id,
                                                                      direct
                                                                      )
                            )
            country = get_country(soup)
            for count in country:
                conn.execute('''INSERT OR IGNORE INTO Movie_Country(imdbID, 
                                                                    Country_imdb 
                                                                    )
                                                                    VALUES (?,?)''',           
                                                                     (imdb_id,
                                                                      count
                                                                      )
                            )
            similar = get_similar(soup)
            for sim in similar:
                conn.execute('''INSERT OR REPLACE INTO Movie_Similar(imdbID, 
                                                                    SimilarMovieID_imdb 
                                                                    )
                                                                    VALUES (?,?)''',           
                                                                     (imdb_id,
                                                                      sim
                                                                      )
                            )
            cast = get_cast(soup)
            for star in cast:
                conn.execute('''INSERT OR IGNORE INTO Movie_Star(imdbID, 
                                                                    Star_imdb 
                                                                    )
                                                                    VALUES (?,?)''',           
                                                                     (imdb_id,
                                                                      star
                                                                      )
                            )
            conn.execute('''DELETE FROM Potential_Movies
                            WHERE imdbID = ? AND Rater = ?''', (imdb_id,rater))
            conn.commit()
        #Exit loop if current movie already in database
        if break_after_page:
            break 
    print("\nDatabase Update Done!")



#Second main function. Creates a dictionary with all SQL data stored for a specific user.
#The dictionary can than be used to create a csv file to train a random forest model


def SQLToMovieDict(profilName):
    conn = sqlite3.connect('Movie_Database.db')
    #Build Imdb Dict from SQL data
    #General imdb data
    cursor = conn.execute(''' SELECT  Movie_imdbData.imdbID, Title_imdb,Rater_imdb, Release_imdb, Runtime_imdb, Rating_imdb
                              FROM Movie_imdbData
                              LEFT JOIN Own_Rating
                              ON Movie_imdbData.imdbID = Own_Rating.imdbID
                              WHERE Rater = ?''', (profilName,))
    movie_dict = {}
    for row in cursor:
        movie_dict[row[0]] = {}
        movie_dict[row[0]]["Title"] = row[1]
        movie_dict[row[0]]["Rater_Count"] = row[2]
        movie_dict[row[0]]["Release"] = row[3]
        movie_dict[row[0]]["Runtime"] = row[4]
        movie_dict[row[0]]["imdb_Rating"] = row[5]
    #Country List
    cursor = conn.execute(''' SELECT  Movie_Country.imdbID, Country_imdb 
                              FROM Movie_Country
                              LEFT JOIN Own_Rating
                              ON Movie_Country.imdbID = Own_Rating.imdbID
                              WHERE Rater = ?''', (profilName,))
    for row in cursor: 
        movie_dict[row[0]]["Country"] = movie_dict[row[0]].get("Country",[]) + [row[1]]
    #Director List
    cursor = conn.execute(''' SELECT  Movie_Director.imdbID, Director_imdb 
                              FROM Movie_Director
                              LEFT JOIN Own_Rating
                              ON Movie_Director.imdbID = Own_Rating.imdbID
                              WHERE Rater = ?''', (profilName,))
    for row in cursor: 
        movie_dict[row[0]]["Director"] = movie_dict[row[0]].get("Director",[]) + [row[1]]
    #Genre List
    cursor = conn.execute(''' SELECT  Movie_Genre.imdbID, Genre_imdb 
                              FROM Movie_Genre
                              LEFT JOIN Own_Rating
                              ON Movie_Genre.imdbID = Own_Rating.imdbID
                              WHERE Rater = ?''', (profilName,))
    for row in cursor: 
        movie_dict[row[0]]["Genre"] = movie_dict[row[0]].get("Genre",[]) + [row[1]]
    #Similar List
    cursor = conn.execute(''' SELECT  Movie_Similar.imdbID, SimilarMovieID_imdb
                              FROM Movie_Similar
                              LEFT JOIN Own_Rating
                              ON Movie_Similar.imdbID = Own_Rating.imdbID
                              WHERE Rater = ?''', (profilName,))
    for row in cursor: 
        movie_dict[row[0]]["SimilarMovie"] = movie_dict[row[0]].get("SimilarMovie",[]) + [row[1]]
    #Star List
    cursor = conn.execute(''' SELECT  Movie_Star.imdbID, Star_imdb
                              FROM Movie_Star
                              LEFT JOIN Own_Rating
                              ON Movie_Star.imdbID = Own_Rating.imdbID
                              WHERE Rater = ?''', (profilName,))
    for row in cursor: 
        movie_dict[row[0]]["Star"] = movie_dict[row[0]].get("Star",[]) + [row[1]]
    #Writer List
    cursor = conn.execute(''' SELECT  Movie_Writer.imdbID, Writer_imdb
                              FROM Movie_Writer
                              LEFT JOIN Own_Rating
                              ON Movie_Writer.imdbID = Own_Rating.imdbID
                              WHERE Rater = ?''', (profilName,))
    for row in cursor: 
        movie_dict[row[0]]["Writer"] = movie_dict[row[0]].get("Writer",[]) + [row[1]]
    #Personal Rating
    cursor = conn.execute(''' SELECT  imdbID, Personal_Rating
                              FROM Own_Rating
                              WHERE Rater = ?''', (profilName,))
    for row in cursor: 
        movie_dict[row[0]]["Personal_Rating"] = row[1]
    return movie_dict
    


#Third main function: movie dict to pandas dataframe. 
#Takes movie_dict from second main function and creates a pandas dataframe with relevant Features (above a certain threshold)

def MovieDictToPandas(movie_dict, profilName):
    movie_pandas_list = []
    relevantCountries = determineCountryVariables(profilName)
    relevantWriter = determineWriterVariables(profilName)
    relevantGenre = determineGenreVariables(profilName)
    relevantStars = determineStarVariables(profilName)
    relevantDirectors = determineDirectorVariables(profilName)
    for row in movie_dict.keys():
        movie = movie_dict.get(row,{})
        single_movie_dict = {"id": row,"Title": movie["Title"],"Rater_Count":movie["Rater_Count"],
                             "imdb_Rating": movie["imdb_Rating"],"Personal_Rating":movie["Personal_Rating"],
                             "Release": movie["Release"],"Runtime": movie["Runtime"]}
        for country in relevantCountries:
            single_movie_dict["Country_"+country] = country in movie["Country"]
        for writer in relevantWriter:
            try:
                single_movie_dict["Writer_"+writer] = writer in movie["Writer"]
            except KeyError:
                single_movie_dict["Writer_"+writer] = False
        for genre in relevantGenre:
            single_movie_dict["Genre_"+genre] = genre in movie["Genre"]
        for star in relevantStars:
            try:
                single_movie_dict["Star_"+star] = writer in movie["Star"]
            except KeyError:
                single_movie_dict["Star_"+star] = False
        for director in relevantDirectors:
            try:
                single_movie_dict["Director_"+director] = writer in movie["Director"]
            except KeyError:
                single_movie_dict["Director_"+director] = False
        single_movie_dict["OscarWinnerMale_Since1980"] = check_OscarWinnerMale(movie.get("Star",[]))
        single_movie_dict["OscarWinnerFemale_Since1980"] = check_OscarWinnerFemale(movie.get("Star",[]))
        single_movie_dict["Similar_Movie_Average"] = get_similarRating(movie_dict, row)
        movie_pandas_list.append(single_movie_dict)
    movie_trainingData = pd.DataFrame(movie_pandas_list)
    return movie_trainingData        
        
        
    
#Create list with all column names of pandas trainin data

def createTrainingFeatureList(profilName):
    relevantCountries = determineCountryVariables(profilName)
    relevantWriter = determineWriterVariables(profilName)
    relevantGenre = determineGenreVariables(profilName)
    relevantStars = determineStarVariables(profilName)
    relevantDirectors = determineDirectorVariables(profilName)
    trainingFeatures = ["Release","imdb_Rating","Runtime","Rater_Count","OscarWinnerMale_Since1980",
                        "OscarWinnerFemale_Since1980", "Similar_Movie_Average"]
    for country in relevantCountries:
        trainingFeatures.append("Country_" + country)
    for writer in relevantWriter:
        trainingFeatures.append("Writer_" + writer)
    for genre in relevantGenre:
        trainingFeatures.append("Genre_" + genre)
    for star in relevantStars:
        trainingFeatures.append("Star_" + star)
    for director in relevantDirectors:
        trainingFeatures.append("Director_" + director)
    return trainingFeatures


#Two function to search imdb for random movies
    
def setImdbSearchParam(page,languages="en",num_votes="1000,",production_status="released",release_date="2005,2016",title_type="feature",user_rating="6.0,10"):
    page = str(page)    
    imdb_serviceurl = "http://www.imdb.com/search/title?"
    search_url = imdb_serviceurl +"languages=" + languages + "&" + "num_votes=" + num_votes + "&" + "production_status=" + production_status + "&" + "release_date=" + release_date + "&" + "title_type=" + title_type + "&" + "user_rating=" + user_rating + "&page=" + page + "&" + "sort=moviemeter,asc"       
    return search_url

    
def getMovieListImdbSearch(search_url,movie_dict):
    movie_page_list = []
    html = urllib.request.urlopen(search_url).read()
    soup = BeautifulSoup(html,'html.parser')
    tag = soup.findAll("div", {"class": "lister-item mode-advanced"})
    for i in tag:
        y = i.find("div", {"class": "ribbonize"})
        y = y['data-tconst']
        y = int(re.sub("tt","",y))
        if y in movie_dict:
            continue
        else:
            movie_page_list.append("http://www.imdb.com/title/tt" + str(y) + "/")
    return movie_page_list   
   
   
   
#Create dict from single movie data to transform it into a pandas dataframe

def createSingleMovieDict(imdb_link,movie_dict,relevantCountries,relevantWriter,relevantGenre,relevantStars,relevantDirectors):      
    html = urllib.request.urlopen(imdb_link).read()
    soup = BeautifulSoup(html, "lxml")    
    imdb_id = re.findall("title/tt(.+)/", imdb_link)
    imdb_id = int(imdb_id[0])
    single_movie_dict = {}
    #get imdb data from link
    #return to start if movie hase no imdb rating
    single_movie_dict["id"] = imdb_id
    single_movie_dict["Title"] = get_title(soup)
    single_movie_dict["Rater_Count"] = get_rater(soup)
    single_movie_dict["Release"] = get_year(soup)
    single_movie_dict["Runtime"] = get_runtime(soup)
    single_movie_dict["imdb_Rating"]  = get_rating(soup)
    movie_genres = get_genres(soup)
    movie_country = get_country(soup)
    movie_director = get_director(soup)
    movie_writer = get_writer(soup)
    movie_star = get_cast(soup)
    for country in relevantCountries:
        single_movie_dict["Country_"+country] = country in movie_country
    for writer in relevantWriter:
        try:
            single_movie_dict["Writer_"+writer] = writer in movie_writer
        except KeyError:
            single_movie_dict["Writer_"+writer] = False
    for genre in relevantGenre:
        single_movie_dict["Genre_"+genre] = genre in movie_genres 
    for star in relevantStars:
        try:
            single_movie_dict["Star_"+star] = writer in movie_star
        except KeyError:
            single_movie_dict["Star_"+star] = False
    for director in relevantDirectors:
        try:
            single_movie_dict["Director_"+director] = writer in movie_director
        except KeyError:
            single_movie_dict["Director_"+director] = False
    similar_ratings = []
    similars = get_similar(soup)
    for similar_movie in similars:
        conn = sqlite3.connect('Movie_Database.db')
        cursor = conn.execute(''' SELECT  Personal_Rating FROM Own_Rating WHERE imdbID == ? AND Rater == ? ''', (similar_movie,profilName))
        rating = cursor.fetchone()
        try:
            similar_ratings.append(rating[0])
        except TypeError:
            continue
    if not similar_ratings:
        single_movie_dict["OscarWinnerMale_Since1980"] = check_OscarWinnerMale(movie_star)
        single_movie_dict["OscarWinnerFemale_Since1980"] = check_OscarWinnerFemale(movie_star)
    else:
        similar_rating = np.mean(similar_ratings)
        single_movie_dict["Similar_Movie_Average"] =  similar_rating
        single_movie_dict["OscarWinnerMale_Since1980"] = check_OscarWinnerMale(movie_star)
        single_movie_dict["OscarWinnerFemale_Since1980"] = check_OscarWinnerFemale(movie_star)
    return single_movie_dict



    
    
print("Hello! I'm your personal movie recommender. I can store your already rated movies in a database, you can ask me how you would like a specific movie and i can automatically search imdb for movies you should watch. Let's start!")
while True:
    profil_id = input("Please insert your filmempfehlungs-ID(Numbers in the link to your profil): ") 
    profilName = get_profilName(profil_id)
    right = input("Is '" + profilName + "' the right username? - write 'y' or 'n': ")
    if right == "y":
        break  
while True:  
    user_decision = input("\nUse one of the following commands:\n'database' - update/create your movie database with new movies\n'recommend' - start the recommender mode\n'break' - quit the program\nYour input: ") 
    if user_decision == "break":
        print("Goodbye!")
        break
    if user_decision == "database":
        print("Add new rated movies to database...")
        filmempfToSQL(profil_id)
        continue
    elif user_decision == "recommend":
        print("Collecting training data...")
        movie_dict = SQLToMovieDict(profilName)
        movie_trainingData = MovieDictToPandas(movie_dict, profilName)
        movie_trainingData_noSimilar = MovieDictToPandas(movie_dict, profilName)
        movie_trainingData[["Runtime","Similar_Movie_Average"]] = movie_trainingData[["Runtime","Similar_Movie_Average"]].apply(pd.to_numeric)
        movie_trainingData_noSimilar[["Runtime"]] = movie_trainingData_noSimilar[["Runtime"]].apply(pd.to_numeric)        
        movie_trainingData_noSimilar.drop("Similar_Movie_Average",axis=1,inplace=True)               
        movie_trainingData = movie_trainingData.dropna()
        movie_trainingData_noSimilar = movie_trainingData_noSimilar.dropna()        
        trainingFeatures = createTrainingFeatureList(profilName)
        trainingFeatures_noSimilar = createTrainingFeatureList(profilName)
        trainingFeatures_noSimilar.remove("Similar_Movie_Average")
        predictors_noSimilar = movie_trainingData_noSimilar[trainingFeatures_noSimilar] 
        targets_noSimilar = movie_trainingData_noSimilar["Personal_Rating"].values
        print("There are overall",len(movie_trainingData.index),"movies with", len(movie_trainingData.columns),"features to train the main algorithm")
        print("There are overall",len(movie_trainingData_noSimilar.index),"movies with", len(movie_trainingData_noSimilar.columns),"features to train the weaker backup algorithm")        
        predictors = movie_trainingData[trainingFeatures]
        targets = movie_trainingData["Personal_Rating"].values
        print("Training random forest model...")
        forest_all = RandomForestRegressor(n_estimators = 3000, max_features = int(len(trainingFeatures)/3))
        forest_noSimilar = RandomForestRegressor(n_estimators = 3000 , max_features = int((len(trainingFeatures)-1)/3))
        forest_all = forest_all.fit(predictors,targets ) 
        forest_noSimilar = forest_noSimilar.fit(predictors_noSimilar,targets_noSimilar ) 
        relevantCountries = determineCountryVariables(profilName)
        relevantWriter = determineWriterVariables(profilName)
        relevantGenre = determineGenreVariables(profilName)
        relevantStars = determineStarVariables(profilName)
        relevantDirectors = determineDirectorVariables(profilName)
        conn = sqlite3.connect('Movie_Database.db')
        print("Done.")
        while True:
            user_input = input("\nUse one of the following commands in the recommend mode:\n'ask' -  ask for the estimated rating for a specific movie.\n'search' -  start a automatic search for potential new movies to watch.\n'update' - calculate new ratings for your already recommended and stored movies.\n'show' - shows the movies in your potential new movie table with the highest estimated rating\n'break' - quit the recommendation mode\nYour input: ")
            if user_input == "show":
                show_input = input("Enter the number of movies you wish to see: " )
                print("\nCurrently the", show_input, "movies with the highest estimated rating in your database for potential new movies are:...")
                cursor = conn.execute('''SELECT  imdbID,Title_imdb,Calculated_Rating FROM Potential_Movies WHERE Rater = ?  ORDER BY Calculated_Rating DESC LIMIT ?''',(profilName,show_input))
                print("\n")                            
                for row in cursor:
                    print("imdbID:",row[0], row[1].strip() ,":", str(row[2])[:6])
            if user_input == "ask":
                while True:
                    imdb_link = input("\nInsert imdb link (Example link: http://www.imdb.com/title/tt1014763/)\nWrite 'break' to quit the ask mode:....\nYour input:   " )
                    if imdb_link == "break":
                        break
                    html = urllib.request.urlopen(imdb_link).read()
                    soup = BeautifulSoup(html, "lxml")
                    imdb_id = re.findall("title/tt(.+)/", imdb_link)
                    imdb_id = int(imdb_id[0])
                    if imdb_id in movie_dict:
                        print("\nMovie already watched!")
                        continue
                    try:
                        if is_series(soup):
                            print("\nSeries are currently not supported. Please choose another movie" )
                            continue
                    except TypeError:
                        print("\nNo proper imdb link! Please insert another link")
                        continue
                    try:    
                        test_rating  = get_rating(soup)
                    except UnboundLocalError:
                        print("\nMovie has no imdb rating. Please choose another movie" )
                        continue
                    single_movie_dict = createSingleMovieDict(imdb_link,movie_dict,relevantCountries,relevantWriter,relevantGenre,relevantStars,relevantDirectors)
                    if "Similar_Movie_Average" not in single_movie_dict:
                        print("\nNot enough similar movies in your personal database. Using weaker backup model")
                        new_movie_data_predictors = pd.DataFrame([single_movie_dict])
                        new_movie_data_predictors = new_movie_data_predictors[trainingFeatures_noSimilar]
                        calculated_rating = forest_noSimilar.predict(new_movie_data_predictors)
                        print("\nYou would rate the movie ", single_movie_dict["Title"].strip(), " with a rating of: ",calculated_rating[0] )
                        if calculated_rating[0] >= 80:                       
                            print("\nSaving calculated rating in database for potential new movies.")
                            cursor = conn.execute('''INSERT OR REPLACE INTO Potential_Movies (imdbID, 
                                                                          Title_imdb,
                                                                          Calculated_Rating,
                                                                          Rater
                                                                          )
                                                                          VALUES (?,?,?,?)''',           
                                                                         (single_movie_dict["id"], 
                                                                          single_movie_dict["Title"],
                                                                          calculated_rating[0],
                                                                          profilName)
                                            )
                            conn.commit()
                        continue
                    else:
                        new_movie_data_predictors = pd.DataFrame([single_movie_dict])
                        new_movie_data_predictors = new_movie_data_predictors[trainingFeatures]
                        calculated_rating = forest_all.predict(new_movie_data_predictors)
                        print("\nYou would rate the movie ", single_movie_dict["Title"].strip(), " with a rating of: ",calculated_rating[0] )
                        if calculated_rating[0] >= 80:                        
                            print("\nSaving movie in database for potential new movies.")
                            cursor = conn.execute('''INSERT OR REPLACE INTO Potential_Movies (imdbID, 
                                                                              Title_imdb,
                                                                              Calculated_Rating,
                                                                              Rater
                                                                              )
                                                                              VALUES (?,?,?,?)''',           
                                                                             (single_movie_dict["id"], 
                                                                              single_movie_dict["Title"],
                                                                              calculated_rating[0],
                                                                              profilName)
                                                )
                            conn.commit() 
            if user_input == "search":
                search_results = {}
                while True:
                    start_page = int(input("Insert starting page: "))
                    for page in range(start_page,65):
                        print("Scraping imdb Search Page number",str(page),"...")
                        search_url = setImdbSearchParam(page)
                        random_movie_list = getMovieListImdbSearch(search_url,movie_dict)
                        for movie in random_movie_list:
                            time.sleep(5)
                            single_movie_dict = createSingleMovieDict(movie,movie_dict,relevantCountries,relevantWriter,relevantGenre,relevantStars,relevantDirectors)
                            if "Similar_Movie_Average" not in single_movie_dict:
                                new_movie_data_predictors = pd.DataFrame([single_movie_dict])
                                new_movie_data_predictors = new_movie_data_predictors[trainingFeatures_noSimilar]
                                calculated_rating = forest_noSimilar.predict(new_movie_data_predictors)
                                print("Movie: ", single_movie_dict["Title"].strip(), " Estimated Rating: ",calculated_rating[0],"similar movie data mising! Probably inaccurate!" )
                                if calculated_rating[0] >= 80:                                
                                    cursor = conn.execute('''INSERT OR REPLACE INTO Potential_Movies (imdbID, 
                                                                                      Title_imdb,
                                                                                      Calculated_Rating,
                                                                                      Rater
                                                                                      )
                                                                                      VALUES (?,?,?,?)''',           
                                                                                     (single_movie_dict["id"], 
                                                                                      single_movie_dict["Title"],
                                                                                      calculated_rating[0],
                                                                                      profilName
                                                                                      )
                                                )
                                    conn.commit()
                                    search_results[single_movie_dict["Title"]] = calculated_rating
                            else:
                                new_movie_data_predictors = pd.DataFrame([single_movie_dict])
                                new_movie_data_predictors = new_movie_data_predictors[trainingFeatures]
                                calculated_rating = forest_all.predict(new_movie_data_predictors)
                                print("Movie: ", single_movie_dict["Title"].strip(), " Estimated Rating: ",calculated_rating[0] )
                                if calculated_rating[0] >= 80:
                                    cursor = conn.execute('''INSERT OR REPLACE INTO Potential_Movies (imdbID, 
                                                                                      Title_imdb,
                                                                                      Calculated_Rating,
                                                                                      Rater
                                                                                      )
                                                                                      VALUES (?,?,?,?)''',           
                                                                                     (single_movie_dict["id"], 
                                                                                      single_movie_dict["Title"],
                                                                                      calculated_rating[0],
                                                                                      profilName
                                                                                      )
                                                )
                                    conn.commit()
                                    search_results[single_movie_dict["Title"]] = calculated_rating
                        print("\nOverall",len(search_results.keys()),"new movies added to potential movie table")
                        user_break = input("\nWrite 'break' to quit the automatic search.\nPress Enter to continue.")
                        if user_break == "break":
                            print("\nSearch results. Following movies added to potential movies:...")
                            for key in search_results.keys():
                                print(key.strip(),":",str(search_results[key][0])[:6])
                            print("\nCurrently the 20 movies with the highest estimated rating in your database for potential new movies are:...")
                            cursor = conn.execute('''SELECT  imdbID,Title_imdb,Calculated_Rating FROM Potential_Movies WHERE Rater = ?  ORDER BY Calculated_Rating DESC LIMIT 20''',(profilName,))
                            print("\n")                            
                            for row in cursor:
                                print("imdbID:",row[0], row[1].strip() ,":", str(row[2])[:6])
                            break
                    if user_break == "break":
                        break
            if user_input == "update":
                cursor = conn.execute('''SELECT imdbID,Calculated_Rating FROM Potential_Movies WHERE Rater = ? AND Calculated_Rating >= 80''', (profilName,))
                cursor = cursor.fetchall()
                print(str(len(cursor)), "movies to update")                
                for row in cursor:
                    time.sleep(5)
                    movie = "http://www.imdb.com/title/tt" + str(row[0]) + "/"
                    single_movie_dict = createSingleMovieDict(movie,movie_dict,relevantCountries,relevantWriter,relevantGenre,relevantStars,relevantDirectors)
                    if "Similar_Movie_Average" not in single_movie_dict:
                        new_movie_data_predictors = pd.DataFrame([single_movie_dict])
                        new_movie_data_predictors = new_movie_data_predictors[trainingFeatures_noSimilar]
                        calculated_rating = forest_noSimilar.predict(new_movie_data_predictors)
                        print("Movie:", single_movie_dict["Title"].strip(), "...Previous Rating:", str(row[1])[:6], "...Estimated Rating: ",str(calculated_rating[0])[:6] )
                        cursor = conn.execute('''INSERT OR REPLACE INTO Potential_Movies (imdbID, 
                                                                          Title_imdb,
                                                                          Calculated_Rating,
                                                                          Rater
                                                                          )
                                                                          VALUES (?,?,?,?)''',           
                                                                         (single_movie_dict["id"], 
                                                                          single_movie_dict["Title"],
                                                                          calculated_rating[0],
                                                                          profilName
                                                                          )
                                    )
                        conn.commit()
                    else:
                        new_movie_data_predictors = pd.DataFrame([single_movie_dict])
                        new_movie_data_predictors = new_movie_data_predictors[trainingFeatures]
                        calculated_rating = forest_all.predict(new_movie_data_predictors)
                        print("Movie:", single_movie_dict["Title"].strip(), "...Previous Rating:", str(row[1])[:6],"...Estimated Rating: ",str(calculated_rating[0])[:6] )
                        cursor = conn.execute('''INSERT OR REPLACE INTO Potential_Movies (imdbID, 
                                                                          Title_imdb,
                                                                          Calculated_Rating,
                                                                          Rater
                                                                          )
                                                                          VALUES (?,?,?,?)''',           
                                                                         (single_movie_dict["id"], 
                                                                          single_movie_dict["Title"],
                                                                          calculated_rating[0],
                                                                          profilName
                                                                          )
                                    )
                        conn.commit()
            if user_input == "break":
                break

            

            
            
            
        
        
