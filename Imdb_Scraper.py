# -*- coding: utf-8 -*-
"""
Created on Thu Sep 29 15:53:45 2016

@author: Tobi
"""

from bs4 import BeautifulSoup
import urllib
import datetime
import re
import sqlite3




class Imdb_Movie():
    
    def __init__(self, imdb_id):
        self.imdb_id = imdb_id
        self.imdb_link = "http://www.imdb.com/title/tt" + str(self.imdb_id) + "/"
        
        self.html = urllib.request.urlopen(self.imdb_link).read()
        self.soup = BeautifulSoup(self.html,"lxml")
        
        self.is_series()
        if not self.is_series:
            try:
                self.get_rating()
                self.get_rater()
            except AttributeError:
                self.rating = -1
                self.rater = -1
            self.get_title()
            self.get_year()
            self.get_runtime()
            self.get_genres()
            self.get_writer()
            self.get_director()
            self.get_country()
            self.get_similar()
            self.get_cast()
            
            self.check_OscarWinnerFemale()
            self.check_OscarWinnerMale()
        
        
    def get_rating(self):
        tags = self.soup("span", itemprop="ratingValue")
        for tag in tags:
            self.rating = float(tag.contents[0])
        return self.rating
    
    
    def get_title(self): 
        title = self.soup.find(attrs={"itemprop" : "name"})
        [s.extract() for s in title('span')]
        self.title = title.text
        return self.title
    
    
    def get_rater(self):
        tags = str(self.soup("span", itemprop="ratingValue"))
        rater = re.findall("<strong title=.+?(\d+,\d+)", tags)
        if rater == []:
            rater = re.findall("<strong title=.+?(\d+)", tags)
        if rater == []:
            tags = str(self.soup("span", itemprop="ratingCount"))
            rater = re.findall('ratingCount">(\d+,\d+)', tags)
        if rater == []:
            rater = re.findall('ratingCount">(\d+)', tags)   
        self.rater = int(rater[0].replace(",",""))
        return self.rater
    
    
    def get_year(self):
        tags = self.soup.find("div", {"class": "subtext"})
        tags = tags.find("meta",attrs={"itemprop" : "datePublished"})["content"]
        if "-" in tags:
            try:
                year = datetime.datetime.strptime(tags,"%Y-%m-%d")
                self.year = year.year
            except ValueError:
                year = datetime.datetime.strptime(tags,"%Y-%m")
                self.year = year.year    
        else:
            self.year = tags
        return int(self.year)
     
         
    def get_runtime(self):
        tags= self.soup("time", itemprop = "duration")
        i = 0
        runtime = None
        for tag in tags:
            runtime = str(tag.contents[0])
            i += 1
            if i == 2:
                break
        if runtime == None:
            self.runtime = ""
        elif "h" in runtime:
            hour = int(runtime[:runtime.find("h")])
            if runtime.find("m") == -1:
                minute = 0
            else:
                minute = int(runtime[runtime.find("h")+2:runtime.find("m")])
            self.runtime = hour * 60 + minute
        else:
            self.runtime = int(runtime.replace(" min",""))
        return self.runtime    
    
           
    def get_genres(self):
        tags= self.soup("span", itemprop = "genre")
        self.genres = []
        for tag in tags:
            self.genres.append(str(tag.contents[0]))
        return self.genres
    
    
    def get_writer(self):
        tags= str(self.soup("span", itemprop ="creator"))
        self.writer = re.findall('Person">\n.+itemprop="name">(.+?)</span', tags)
        return self.writer
    
           
    def get_director(self):
        tags= str(self.soup("span", itemprop ="director"))
        self.director = re.findall('itemprop="name">(.+?)</span', tags)  
        return self.director
    
    
    def get_country(self):
        tags = self.soup.find_all("div", attrs= {"class": "txt-block"})
        for tag in tags:
           if tag.find("h4").text == "Country:":
               tags = tag
               break
        tags = tags.find_all("a")
        self.country = []
        for tag in tags:
            self.country.append(tag.text)
        return self.country
    
    
    def get_similar(self):
        tags= self.soup.findAll("div", { "class" : "rec_item" })
        self.similars = []
        for i in tags:
            y = i['data-tconst']
            y = int(re.sub("tt","",y))
            self.similars.append(y)
        return self.similars
    
    
    def get_cast(self):
        tags= str(self.soup("table", { "class" : "cast_list" }))
        self.cast= re.findall('title="(.+?)"', tags)
        return self.cast
        
    
    def is_series(self):
        tags = self.soup.find("meta",{"name":"title"})["content"]
        self.is_series = "Series" in tags or "series" in tags
        return self.is_series
    
    
    def check_OscarWinnerMale(self):
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
        self.OscarWinnerMaleInCast = False
        while True:
            try:
                for values in self.cast:
                    if values in Oscar_Winner_Male:
                        self.OscarWinnerMaleInCast = True
                        return self.OscarWinnerMaleInCast
                return self.OscarWinnerMaleInCast
                break
            except KeyError:
                return self.OscarWinnerMaleInCast
                break
            except AttributeError:
                self.get_cast()

            
    def check_OscarWinnerFemale(self):
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
        self.OscarWinnerFemaleInCast = False
        while True:
            try:
                for values in self.cast:
                    if values in Oscar_Winner_Female:
                        self.OscarWinnerFemaleInCast = True
                        return self.OscarWinnerFemaleInCast
                return self.OscarWinnerFemaleInCast
                break
            except KeyError:
                return self.OscarWinnerFemaleInCast
                break
            except AttributeError:
                self.get_cast()







class Database_Movie(Imdb_Movie):
    
    
    def __init__(self,imdb_id):
        self.imdb_id = imdb_id
        self.imdb_link = "http://www.imdb.com/title/tt" + str(self.imdb_id) + "/"

        self.get_rating()
        self.get_rater()
        self.get_title()
        self.get_year()
        self.get_runtime()
        self.get_genres()
        self.get_writer()
        self.get_director()
        self.get_country()
        self.get_similar()
        self.get_cast()
        
        self.check_OscarWinnerFemale()
        self.check_OscarWinnerMale()
        
        
    def get_rating(self):
        conn = sqlite3.connect('Movie_Database.db')
        cursor = conn.execute(''' SELECT  Movie_imdbData.imdbID, Rating_imdb
                                  FROM Movie_imdbData
                                  WHERE Movie_imdbData.imdbID = ? ''', (self.imdb_id,))
        for row in cursor:
            self.rating = float(row[1])
        conn.close()
        return self.rating
    
    
    def get_rater(self):
        conn = sqlite3.connect('Movie_Database.db')
        cursor = conn.execute(''' SELECT  Movie_imdbData.imdbID, Rater_imdb
                                  FROM Movie_imdbData
                                  WHERE Movie_imdbData.imdbID = ? ''', (self.imdb_id,))
        for row in cursor:
            self.rater = int(row[1])
        conn.close()
        return self.rater
    
    
    def get_title(self):
        conn = sqlite3.connect('Movie_Database.db')
        cursor = conn.execute(''' SELECT  Movie_imdbData.imdbID, Title_imdb
                                  FROM Movie_imdbData
                                  WHERE Movie_imdbData.imdbID = ? ''', (self.imdb_id,))
        for row in cursor:
            self.title = str(row[1])
        conn.close()
        return self.title
    
    
    def get_year(self):
        conn = sqlite3.connect('Movie_Database.db')
        cursor = conn.execute(''' SELECT  Movie_imdbData.imdbID, Release_imdb
                                  FROM Movie_imdbData
                                  WHERE Movie_imdbData.imdbID = ? ''', (self.imdb_id,))
        for row in cursor:
            self.year = int(row[1])
        conn.close()
        return self.year
    
    
    def get_runtime(self):
        conn = sqlite3.connect('Movie_Database.db')
        cursor = conn.execute(''' SELECT  Movie_imdbData.imdbID, Runtime_imdb
                                  FROM Movie_imdbData
                                  WHERE Movie_imdbData.imdbID = ? ''', (self.imdb_id,))
        for row in cursor:
            self.runtime = int(row[1])
        conn.close()
        return self.runtime
    
    
    def get_genres(self):
        conn = sqlite3.connect('Movie_Database.db')
        cursor = conn.execute(''' SELECT  imdbID, Genre_imdb
                                  FROM Movie_Genre
                                  WHERE imdbID = ? ''', (self.imdb_id,))
        self.genres = []
        for row in cursor:
            self.genres.append(row[1])
        conn.close()
        return self.genres
    
    
    def get_writer(self):
        conn = sqlite3.connect('Movie_Database.db')
        cursor = conn.execute(''' SELECT  imdbID, Writer_imdb
                                  FROM Movie_Writer
                                  WHERE imdbID = ? ''', (self.imdb_id,))
        self.writer = []
        for row in cursor:
            self.writer.append(row[1])
        conn.close()
        return self.writer
    
    
    def get_director(self):
        conn = sqlite3.connect('Movie_Database.db')
        cursor = conn.execute(''' SELECT  imdbID, Director_imdb
                                  FROM Movie_Director
                                  WHERE imdbID = ? ''', (self.imdb_id,))
        self.director = []
        for row in cursor:
            self.director.append(row[1])
        conn.close()
        return self.director
    
    
    def get_country(self):
        conn = sqlite3.connect('Movie_Database.db')
        cursor = conn.execute(''' SELECT  imdbID, Country_imdb
                                  FROM Movie_Country
                                  WHERE imdbID = ? ''', (self.imdb_id,))
        self.country = []
        for row in cursor:
            self.country.append(row[1])
        conn.close()
        return self.country
    
    
    def get_similar(self):
        conn = sqlite3.connect('Movie_Database.db')
        cursor = conn.execute(''' SELECT  imdbID, SimilarMovieID_imdb
                                  FROM Movie_Similar
                                  WHERE imdbID = ? ''', (self.imdb_id,))
        self.similars = []
        for row in cursor:
            self.similars.append(row[1])
        conn.close()
        return self.similars
    
    
    def get_cast(self):
        conn = sqlite3.connect('Movie_Database.db')
        cursor = conn.execute(''' SELECT  imdbID, Star_imdb
                                  FROM Movie_Star
                                  WHERE imdbID = ? ''', (self.imdb_id,))
        self.cast = []
        for row in cursor:
            self.cast.append(row[1])
        conn.close()
        return self.cast
    
    



class Imdb_RandomSearch():
    
    imdb_serviceurl = "http://www.imdb.com/search/title?"

    
    
    def __init__(self, search_page):
        self.search_page = search_page
        self.languages = "en"
        self.num_votes = "1000,"
        self.production_status = "released"
        self.release_date = "2006,2016"
        self.title_type = "feature"
        self.user_rating = "6.5,10"
        self.GenerateSearchUrl()
        self.scanned_movies = []
        self.added_movies = {}
        self.genre_list = ["action","adventure","animation","biography",
                           "comedy","crime","drama","family","fantasy",
                           "history","horror","music","musical","mystery",
                           "romance","sci-fi","sport","thriller","war","western"]
        
        
    def GenerateSearchUrl(self, added_genre = ""):
        page = str(self.search_page)    
        self.search_url = self.imdb_serviceurl +"languages=" + self.languages + "&" + "num_votes=" + self.num_votes + "&" + "production_status=" + self.production_status + "&" + "release_date=" + self.release_date + "&" + "title_type=" + self.title_type + "&" + "user_rating=" + self.user_rating + "&page=" + page + "&" + "sort=moviemeter,asc" + "&genres=" + added_genre 
        return self.search_url
    
        
    def getMovieListForSearchSite(self,movie_dict):
        self.movie_page_list = []
        html = urllib.request.urlopen(self.search_url).read()
        soup = BeautifulSoup(html,'html.parser')
        tag = soup.findAll("div", {"class": "lister-item mode-advanced"})
        for i in tag:
            imdb_id = i.find("div", {"class": "ribbonize"})
            imdb_id = imdb_id['data-tconst']
            imdb_id = int(re.sub("tt","",imdb_id))
            if imdb_id in movie_dict or imdb_id in self.scanned_movies:
                continue
            else:
                self.movie_page_list.append(imdb_id)
                self.scanned_movies.append(imdb_id)
        return self.movie_page_list  