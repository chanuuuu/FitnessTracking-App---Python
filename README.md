# FitnessTracking-App---Python

FitnessTracking is a Python based web application that allows users to track their fitness activity over a period of time and plots the results over the charts.


Description:
------------

Solution consists of three folders covering pass,credit and distinction specifications.
Pass folder : This covers consists of web service that returns the json data for the given url.
Credit folder: This contains the code that provide offline functionality to the application
Distinction folder: This adds the openid based authentication to the application

INSTALLATION GUIDE:
Following external libraries should be installed for the execution of the solution: (Assumes common libraries/modules like cgi, json, collections etc., sqlite, python 2.7+ installed on the system)

SQLALCHEMY
----------
On Mac OS X:
using easy_install : $easy_install sqlalchemy
FLASK-OPENID
------------
On Mac OS X :
using easy_install : $easy_install Flask-OpenID using pip : $pip install Flask-OpenID

￼How to run DISTINCTION AP
-------------------------
Follow the following instructions to run the Distinction app-
$ python
>>>import server.py
>>>server.init_db()
Now the run server.py.
Go to browser and enter the following url :
http://127.0.0.1:5000
It will redirect to login page if you are not logged in and asks to enter your openid.
Note: This application works good with yahoo open id and google openid.

Offline Application :
Offline functionality of the application allows to do the following even if the application is offline :
See the names of all series
Enter a new value for any series and have these values sent to server when we go back to online and refreshes the browser

