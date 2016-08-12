# -*- coding: utf-8 -*-

import re
import datetime
import pandas as pd
from sklearn.ensemble import RandomForestRegressor



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

#Training a Random Forest Model

forest = RandomForestRegressor(n_estimators = 4000)
forest = forest.fit(predictors,targets )        
