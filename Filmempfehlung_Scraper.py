# -*- coding: utf-8 -*-
"""
Created on Thu Sep 29 15:58:14 2016

@author: Tobi
"""

from bs4 import BeautifulSoup
import urllib
import re
import time



class FilmempfehlungUser():
    
    service_url = "http://www.filmempfehlung.com/"
    
    def __init__(self,profil_id):
        self.profil_id = profil_id
        self.current_page_site = 1
        
        link = "http://www.filmempfehlung.com/profil," + str(self.profil_id) + "_bewertungen~1.html"
        html = urllib.request.urlopen(link).read()
        soup = BeautifulSoup(html,'html.parser')
        
        self.get_lastProfilePageSite(soup)
        self.get_profilName(self.profil_id, soup)
        self.movie_dict = {}
        
        
    def get_profilName(self, profil_id, soup):
        tag = soup.find("div", {"class": "userbild"})
        tag = tag.find("a")
        self.profil_name = tag["title"]
        return self.profil_name
    
    
    def get_lastProfilePageSite(self, soup):
        tag = soup.find("div", {"class" : "seitennavi"})
        tag = tag.findAll("a", {"class" : "seiten1"})
        self.profil_pages = []
        for i in tag:
            if i.text.isdigit():
                self.profil_pages.append(int(i.text))
        self.profil_pages = sorted(self.profil_pages, reverse = True)
        self.last_profil_page = self.profil_pages[0]
        return self.last_profil_page
        
    
    def get_imdbLink(self, link):
        tries = 0
        successful = False
        while not successful:
            try:
                html = urllib.request.urlopen(link).read()
                soup = BeautifulSoup(html,'html.parser')
                imdb = soup.find("a",{"class" : "imdb"})
                imdb_link = imdb["href"]
                successful = True
                return imdb_link
            except urllib.error.URLError:
                tries += 1
                if tries >= 4:
                    break
                print("Connection lost. Reconnecting... Try", tries)
                time.sleep(15)

        
    def get_imdbID(self, imdb_link):
        imdb_id = re.findall("title/tt(.+)", imdb_link)
        imdb_id = int(imdb_id[0])
        return imdb_id
        
    
    def get_MovieDictFromCurrentPage(self):
        print("Current Filmempfehlung.com Page :", self.current_page_site)
        link = self.service_url + "profil,"+ self.profil_id +"_bewertungen~" + str(self.current_page_site) + ".html"
        html = urllib.request.urlopen(link).read()
        soup = BeautifulSoup(html,"lxml")
        for movie in  soup.find_all("div",{"class": "float_left tc bewcov"}):
            rating = movie.find("div", {"class": "tc mt10 mb0"}).text
            rating = re.sub("%","",rating)
            rating = int(rating)
            movie_tags = movie.find("a")
            link = movie_tags["href"]
            link = self.service_url + link
            filmempfhelung_id = re.findall('filme,(\d+)\.',link)
            filmempfhelung_id = int(filmempfhelung_id[0])
            self.movie_dict[filmempfhelung_id] = {}
            self.movie_dict[filmempfhelung_id]["Rating"] = rating
            self.movie_dict[filmempfhelung_id]["Link"] = link
            self.movie_dict[filmempfhelung_id]["imdb_Link"] = self.get_imdbLink(link)
            time.sleep(6)

    
    def switchToNextProfilPage(self):
        if self.current_page_site == self.last_profil_page:
            print("Reached last profil page!")
        else:
            self.current_page_site = self.current_page_site + 1
    