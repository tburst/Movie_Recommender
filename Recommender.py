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

#Defining a function to calcualte an average rating of similar movies and two functions 
#to check for specific genre and country in movie data

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
    return numpy.mean(ratings)


def check_Genre(film_dict,genre):
    return genre in film_dict["Genre"]
    

def check_Country(film_dict,country):
    return country in film_dict["Country"]  
    
    
        
#Functions to work with filmempfehlung.com data. 
        
#Takes desired page of movie site(default start is  page 1) and returns personal
#rating, imdb link and filmempfehlungs-id as dict

def get_ownMovieList(profil_id,page_site=1):
    service_url = "http://www.filmempfehlung.com/"
    page_site = str(page_site)
    link = service_url + "profil,"+profil_id+"_bewertungen~" + page_site + ".html"
    html = urllib.request.urlopen(link).read()
    soup = BeautifulSoup(html,'html.parser', "lxml")
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
    conn.execute('''CREATE TABLE IF NOT EXISTS Potential_Movies(imdbID NUMERIC PRIMARY KEY,
                                                                Title_imdb VARCHAR(30),
                                                                Calculated_Rating NUMERIC)''')
    #Get all movies already saved in database
    cursor = conn.execute(''' SELECT  imdbID FROM Own_Rating WHERE Rater = ? ''',(profilName,))
    rated_movies = []
    for row in cursor:
        rated_movies.append(row[0])
    #Loop over all profil pages to store movies in database
    for i in range(1, last_page + 1):
        print("Filmempfehlung.com Profil Page:",i)
        personal_movie_dict = get_ownMovieList(profil_id,i)
        for movie in personal_movie_dict.keys():
            print("FilmempfehlungsID:", movie)
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
            if imdb_id in rated_movies:
                print("Movie with id",movie, "already in database!")
                break
            rater = profilName
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
            print(title)
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
            conn.commit()
            time.sleep(5)
        #Exit loop if current movie already in database
        if imdb_id in rated_movies:
            print("Database Update Done!")
            break 



#Second main function. Creates a dictionary with all SQL data stored for a specific user.
#The dictionary can than be used to create a csv file to train a random forest model


def SQLToMovieDict(profil_id):
    profil_id = str(profil_id)
    profilName = get_profilName(profil_id)
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
    



    
    
#Reading Labled Movie Data in Panda Dataframe
#Features with single actors or directors are based on their count. 
#E.g. every actor who played in ten or more movies in the training data got an own variable 

train_data = pd.read_csv('CurrentMovieData.csv', header = 0, encoding = "ISO-8859-1")
train_data = train_data.dropna()
predictors = train_data[[   "Release","imdbRating","Runtime",
                    "Rater","Genre_Drama","Genre_Comedy",
                    "Genre_Thriller","Genre_Action","Genre_Romance",
                    "Genre_Crime","Genre_Adventure","Genre_Biography",
                    "Genre_Mystery","Genre_Sci-Fi","Genre_Fantasy",
                    "Genre_Horror","Genre_History","Genre_Music",
                    "Genre_War","Genre_Sport","Genre_Family",
                    "Genre_Musical","Genre_Documentary","Genre_Western",
                    "Genre_Animation","Genre_Adult","Country_USA",
                    "Country_UK", "Country_France","Country_Germany",
                    "Country_Canada", "Country_Spain", "Country_Belgium",
                    "Country_Australia","Country_Italy","Country_China",
                    "Country_Sweden","Country_Denmark","Country_Japan",
                    "Country_Austria","Country_Switzerland","Country_South Africa",
                    "Country_Ireland", "Country_Netherlands","Country_Hong Kong",
                    "Director_Clint Eastwood", "Director_Ridley Scott","Director_Steven Spielberg",
                    "Director_Steven Soderbergh", "Director_Lasse Hallström","Director_Oliver Stone",
                    "Director_Peter Jackson","Writer_Luc Besson","Writer_Akiva Goldsman",
                    "Writer_Fran Walsh","Writer_Brian Helgeland","Writer_Ethan Coen",
                    "Writer_Woody Allen","Star_Morgan Freeman", "Star_Samuel L. Jackson",
                    "Star_Matt Damon","Star_Robert De Niro","Star_Stellan Skarsgard",
                    "Star_Mark Strong", "Star_Ben Kingsley", "Star_Bruce Willis",
                    "Star_Russell Crowe", "Star_Tom Hanks","Star_Cate Blanchett",
                    "Star_J.K. Simmons","Star_James Franco","Star_Liam Neeson",
                    "Star_Nicole Kidman","Star_Scarlett Johansson","Star_Sigourney Weaver",
                    "Star_Angelina Jolie","Star_Colin Firth","Star_Ewan McGregor",
                    "Star_Jason Statham","Star_Jude Law","Star_Keira Knightley",
                    "Star_Leonardo DiCaprio", "Star_Mark Wahlberg","Star_Patricia Clarkson",
                    "Star_Woody Harrelson","Star_Brad Pitt","Star_Channing Tatum",
                    "Star_David Thewlis", "Star_Ed Harris","Star_Michael Caine",
                    "Star_Nicolas Cage", "Star_Stanley Tucci","OscarWinnerMale_Since1980",
                    "OscarWinnerFemale_Since1980", "Similar_Movie_Average"]]
targets = train_data["OwnRating"].values
predictors.shape
targets.shape

#Training Random Forest Model

print("Building random forest model...")
forest = RandomForestRegressor(n_estimators = 4000)
forest = forest.fit(predictors,targets )        


#Starting loop to insert imdb links and return calculated rating

profil_id = input("Insert your filmempfehlungs-id(Numbers in the link to your profil): ")

while True:
    #ask for imdb link. Quit loop if user writes break
    imdb_link = input("\nInsert imdb link (Example link: http://www.imdb.com/title/tt1014763/)\nWrite break to quit the program:....\n  " )
    if imdb_link == "break":
        break
    #try to open given imdb link with beautifulsoup
    #return to start if link is a series or if link isnt a correct imdb link
    html = urllib.request.urlopen(imdb_link).read()
    soup = BeautifulSoup(html, "lxml")
    try:
        if is_series(soup):
            print("\nSeries are currently not supported. Please choose another movie" )
            continue
    except TypeError:
        print("\nNo proper imdb link! Please insert another link")
        continue
    #get imdb data from link
    #return to start if movie hase no imdb rating
    imdb_id = re.findall("title/tt(.+)/", imdb_link)
    imdb_id = int(imdb_id[0])
    title = get_title(soup)
    release = get_year(soup)
    try:    
        imdb_rating = get_rating(soup)
    except UnboundLocalError:
        print("\nMovie has no imdb rating. Please choose another movie" )
        continue
    runtime = get_runtime(soup)
    rater = get_rater(soup)
    genre = get_genres(soup)
    drama = "Drama" in genre
    comedy = "Comedy" in genre
    thriller = "Thriller" in genre
    action = "Action" in genre
    romance = "Romance" in genre
    crime = "Crime" in genre
    adventure = "Adventure" in genre
    bio = "Biography" in genre
    mystery = "Mystery" in genre
    scifi = "Sci-Fi" in genre
    fantasy = "Fantasy" in genre
    horror = "Horror" in genre
    history = "History" in genre        
    music = "Music" in genre 
    war = "War" in genre 
    sport = "Sport" in genre 
    family = "Family" in genre 
    musical = "Musical" in genre         
    docu = "Documentary" in genre
    western = "Western" in genre
    animation = "Animation" in genre
    adult = "Adult" in genre
    country = get_country(soup)
    usa = "USA" in country
    uk = "UK" in country
    france = "France" in country
    germany = "Germany" in country
    canada = "Canada" in country
    spain = "Spain" in country
    belgium = "Belgium" in country
    australia = "Australia" in country
    italy = "Italy" in country
    china = "China" in country
    sweden = "Sweden" in country
    denmark = "Denmark" in country
    japan = "Japan" in country
    austria = "Austria" in country
    switzerland = "Switzerland" in country
    southafrica = "South Africa" in country
    ireland = "Ireland" in country
    netherlands = "Netherlands" in country
    hongkong = "Hong Kong" in country
    director = get_director(soup)
    clinteastwood = "Clint Eastwood" in director
    ridleyscott = "Ridley Scott" in director
    spielberg = "Steven Spielberg" in director
    soderbergh = "Steven Soderbergh" in director
    hallstroem = "Lasse Hallström" in director
    oliverstone = "Oliver Stone" in director
    peterjackson = "Peter Jackson" in director
    writer = get_writer(soup)
    lucbesson = "Luc Besson" in writer
    goldsman = "Akiva Goldsman" in writer
    walsh = "Fran Walsh" in writer
    helgeland = "Brian Helgeland" in writer
    ethancoen = "Ethan Coen" in writer
    woodyallen = "Woody Allen" in writer
    star = get_cast(soup)
    freeman = "Morgan Freeman" in star
    jackson = "Samuel L. Jackson" in star
    damon = "Matt Damon" in star
    niro = "Robert De Niro" in star
    stellan = "Stellan Skarsgård" in star
    strong = "Mark Strong" in star
    kingsley = "Ben Kingsley" in star
    willis = "Bruce Willis" in star
    crowe = "Russell Crowe" in star        
    hanks = "Tom Hanks" in star
    cate = "Cate Blanchett" in star
    simmons = "J.K. Simmons" in star
    franco = "James Franco" in star
    neeson = "Liam Neeson" in star
    kidman = "Nicole Kidman" in star
    johansson = "Scarlett Johansson" in star        
    weaver = "Sigourney Weaver" in star
    jolie = "Angelina Jolie" in star
    firth = "Colin Firth" in star
    ewan = "Ewan McGregor" in star
    statham = "Jason Statham" in star
    jude = "Jude Law" in star
    keira = "Keira Knightley" in star
    caprio = "Leonardo DiCaprio" in star
    wahlberg = "Mark Wahlberg" in star
    clarkson = "Patricia Clarkson" in star
    harrelson = "Woody Harrelson" in star
    pitt = "Brad Pitt" in star
    tatum = "Channing Tatum" in star
    thewlis = "David Thewlis" in star
    harris = "Ed Harris" in star
    caine = "Michael Caine" in star
    cage = "Nicolas Cage" in star
    tucci = "Stanley Tucci" in star
    oscarmale = check_OscarWinnerMale(star)
    oscarfemale = check_OscarWinnerFemale(star)
    #check for every similar movie if it has a personal rating in the database
    #return average over all returned personal ratings
    similars = get_similar(soup)
    conn = sqlite3.connect('Movie_Database.db')
    rated_movies = []
    cursor = conn.execute(''' SELECT  imdbID FROM Own_Rating ''')
    for row in cursor:
        rated_movies.append(row[0])
    if imdb_id in rated_movies:
        cursor = conn.execute(''' SELECT  Personal_Rating FROM Own_Rating WHERE imdbID == ?''', (imdb_id,))
        rating = cursor.fetchone()
        print("\nMovie already watched. (You rated it with ", rating[0], "points if you can't remember). Please choose another movie")
        continue
    similar_ratings = []
    for similar_movie in similars:
        cursor = conn.execute(''' SELECT  Personal_Rating FROM Own_Rating WHERE imdbID == ?''', (similar_movie,))
        rating = cursor.fetchone()
        try:
            similar_ratings.append(rating[0])
        except TypeError:
            continue
    if not similar_ratings:
        print("\nNot enough similar movies in your personal database. Please choose another movie")
        continue
    similar_rating = np.mean(similar_ratings)
    if np.isnan(similar_rating):
        print("\nNot enough similar movies in your personal database. Please choose another movie")
        continue
    attribut_dict = [{"Release" : release ,"imdbRating" : imdb_rating,"Runtime" : runtime,
                    "Rater" : rater,"Genre_Drama" : drama,"Genre_Comedy":comedy,
                    "Genre_Thriller":thriller,"Genre_Action":action,"Genre_Romance":romance,
                    "Genre_Crime" : crime,"Genre_Adventure" : adventure,"Genre_Biography" : bio,
                    "Genre_Mystery" : mystery,"Genre_Sci-Fi" : scifi,"Genre_Fantasy" : fantasy,
                    "Genre_Horror" : horror,"Genre_History" : history,"Genre_Music" : music,
                    "Genre_War" : war,"Genre_Sport" : sport,"Genre_Family" : family,
                    "Genre_Musical" : musical,"Genre_Documentary" : docu,"Genre_Western" : western,
                    "Genre_Animation" : animation,"Genre_Adult" : adult,"Country_USA" : usa,
                    "Country_UK" : uk, "Country_France" : france,"Country_Germany" : germany,
                    "Country_Canada" : canada, "Country_Spain" : spain, "Country_Belgium" : belgium,
                    "Country_Australia" : australia,"Country_Italy" : italy,"Country_China" : china,
                    "Country_Sweden" : sweden,"Country_Denmark" : denmark,"Country_Japan" : japan,
                    "Country_Austria" : austria,"Country_Switzerland" : switzerland,"Country_South Africa" : southafrica,
                    "Country_Ireland" : ireland, "Country_Netherlands" : netherlands,"Country_Hong Kong" : hongkong,
                    "Director_Clint Eastwood" : clinteastwood, "Director_Ridley Scott" : ridleyscott,"Director_Steven Spielberg" : spielberg,
                    "Director_Steven Soderbergh" : soderbergh, "Director_Lasse Hallström" : hallstroem,"Director_Oliver Stone" : oliverstone,
                    "Director_Peter Jackson" : peterjackson,"Writer_Luc Besson" : lucbesson,"Writer_Akiva Goldsman" : goldsman,
                    "Writer_Fran Walsh" : walsh,"Writer_Brian Helgeland" : helgeland,"Writer_Ethan Coen" : ethancoen,
                    "Writer_Woody Allen" : woodyallen,"Star_Morgan Freeman" : freeman, "Star_Samuel L. Jackson" : jackson,
                    "Star_Matt Damon" : damon,"Star_Robert De Niro" : niro,"Star_Stellan Skarsgard" : stellan,
                    "Star_Mark Strong" : strong, "Star_Ben Kingsley" : kingsley, "Star_Bruce Willis" : willis,
                    "Star_Russell Crowe" : crowe, "Star_Tom Hanks" : hanks,"Star_Cate Blanchett" : cate,
                    "Star_J.K. Simmons" : simmons,"Star_James Franco" : franco,"Star_Liam Neeson" : neeson,
                    "Star_Nicole Kidman" : kidman,"Star_Scarlett Johansson" : johansson,"Star_Sigourney Weaver" : weaver,
                    "Star_Angelina Jolie" : jolie,"Star_Colin Firth" : firth,"Star_Ewan McGregor" : ewan,
                    "Star_Jason Statham" : statham,"Star_Jude Law" : jude,"Star_Keira Knightley" : keira,
                    "Star_Leonardo DiCaprio" : caprio, "Star_Mark Wahlberg" : wahlberg,"Star_Patricia Clarkson" : clarkson,
                    "Star_Woody Harrelson" : harrelson,"Star_Brad Pitt" : pitt,"Star_Channing Tatum" : tatum,
                    "Star_David Thewlis" : thewlis, "Star_Ed Harris" : harris,"Star_Michael Caine" : caine,
                    "Star_Nicolas Cage" : cage, "Star_Stanley Tucci" : tucci,"OscarWinnerMale_Since1980" : oscarmale,
                    "OscarWinnerFemale_Since1980" : oscarfemale, "Similar_Movie_Average" : similar_rating}]
    new_movie_data = pd.DataFrame(attribut_dict)
    new_movie_data_predictors = new_movie_data[["Release","imdbRating","Runtime",
                    "Rater","Genre_Drama","Genre_Comedy",
                    "Genre_Thriller","Genre_Action","Genre_Romance",
                    "Genre_Crime","Genre_Adventure","Genre_Biography",
                    "Genre_Mystery","Genre_Sci-Fi","Genre_Fantasy",
                    "Genre_Horror","Genre_History","Genre_Music",
                    "Genre_War","Genre_Sport","Genre_Family",
                    "Genre_Musical","Genre_Documentary","Genre_Western",
                    "Genre_Animation","Genre_Adult","Country_USA",
                    "Country_UK", "Country_France","Country_Germany",
                    "Country_Canada", "Country_Spain", "Country_Belgium",
                    "Country_Australia","Country_Italy","Country_China",
                    "Country_Sweden","Country_Denmark","Country_Japan",
                    "Country_Austria","Country_Switzerland","Country_South Africa",
                    "Country_Ireland", "Country_Netherlands","Country_Hong Kong",
                    "Director_Clint Eastwood", "Director_Ridley Scott","Director_Steven Spielberg",
                    "Director_Steven Soderbergh", "Director_Lasse Hallström","Director_Oliver Stone",
                    "Director_Peter Jackson","Writer_Luc Besson","Writer_Akiva Goldsman",
                    "Writer_Fran Walsh","Writer_Brian Helgeland","Writer_Ethan Coen",
                    "Writer_Woody Allen","Star_Morgan Freeman", "Star_Samuel L. Jackson",
                    "Star_Matt Damon","Star_Robert De Niro","Star_Stellan Skarsgard",
                    "Star_Mark Strong", "Star_Ben Kingsley", "Star_Bruce Willis",
                    "Star_Russell Crowe", "Star_Tom Hanks","Star_Cate Blanchett",
                    "Star_J.K. Simmons","Star_James Franco","Star_Liam Neeson",
                    "Star_Nicole Kidman","Star_Scarlett Johansson","Star_Sigourney Weaver",
                    "Star_Angelina Jolie","Star_Colin Firth","Star_Ewan McGregor",
                    "Star_Jason Statham","Star_Jude Law","Star_Keira Knightley",
                    "Star_Leonardo DiCaprio", "Star_Mark Wahlberg","Star_Patricia Clarkson",
                    "Star_Woody Harrelson","Star_Brad Pitt","Star_Channing Tatum",
                    "Star_David Thewlis", "Star_Ed Harris","Star_Michael Caine",
                    "Star_Nicolas Cage", "Star_Stanley Tucci","OscarWinnerMale_Since1980",
                    "OscarWinnerFemale_Since1980", "Similar_Movie_Average"]]
    calculated_rating = forest.predict(new_movie_data_predictors)
    print("You would rate the movie ", title, " with a rating of: ",calculated_rating[0] )
    cursor = conn.execute('''INSERT OR IGNORE INTO Potential_Movies (imdbID, 
                                                              Title_imdb,
                                                              Calculated_Rating
                                                              )
                                                              VALUES (?,?,?)''',           
                                                             (imdb_id, 
                                                              title,
                                                              calculated_rating[0]
                                                              )
                        )
    conn.commit()