# -*- coding: utf-8 -*-

import re
import datetime



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
        
        
