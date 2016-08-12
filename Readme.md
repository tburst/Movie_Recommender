Takes as input a Sqlite Database and a Csv-File, both containing personal ratings for movies merged with imdb data. Uses this data as a training-dataset to build a random forest model and returns for every new movie (asked via inserted imdb-link) a calculated rating.

###Already done
Added functions to work with imdb sites and scrape imdb data. 
Added commands to read a csv file with labeld movie data as a pandas data frame and to train a random forest model build on that data.


###To Do
* Add a function to automatically determine  fitting features instead of defining features by hand. Function could count the occurence of every actor and build a feature for every single actor above a threshold
* Add user control. User can decide if he wants to update his database/training data or if he wants to get a specific movie rating.
* Add some kind of automatic search and recommendation for fitting movies. User can start a search for new movie ideas and the programm searches imdb lists, calculates ratings and recommends new movies based on that search.  
