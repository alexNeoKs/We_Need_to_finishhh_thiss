#Import Statements
from asyncio.windows_events import NULL
from lib2to3.pgen2 import driver
from flask import Blueprint, render_template, request

import folium
import pandas as pd
import requests

import haversine
import os
import pickle

from sqlalchemy import null
from .nodes import *
import random
from .dijkstra import *

import sqlite3
from sqlite3 import Error

from time import time, sleep

#This defines the file as our blueprint
#Easier to name it the same as ur file
map = Blueprint('map', __name__)  

#This runs the oneMap Api to retrive addresses data
def OneMapAPI_data_retreive(address):
    req = requests.get('https://developers.onemap.sg/commonapi/search?searchVal='+address+'&returnGeom=Y&getAddrDetails=Y&pageNum=1')
    resultsdict = eval(req.text)
    
    return resultsdict

#Building the referencing dataset(excel) to build dataset

new_dict_data_all = null
datastore = {}
nodesArray = getNodesArray()
distanceGraph = Graph(nodesArray)
filename = 'dataset_of_postal'

if os.path.isfile('dataset_of_postal'):
    print ("File exist")
    infile = open(filename,'rb')
    new_dict_data_all = pickle.load(infile)
    infile.close()
else:
    print ("File not exist")

    df = pd.read_csv("hdb-property-information.csv")
    df['Address'] = df['blk_no'] + " " + df['street']
    addresslist = list(df['Address'])[:12472]
    postal = []   
    for i in addresslist:
        postal.append(OneMapAPI_data_retreive(i))
    for k in range(len(addresslist)):
        datastore[k] = postal[k]
    outfile = open(filename,'wb')

    pickle.dump(datastore,outfile)
    outfile.close()


def Check_Valid_User_Input(User_Input):
    for i in range(len(new_dict_data_all)):
        if (bool(new_dict_data_all[i]['results']) == False or bool(new_dict_data_all[i]) == False):
            continue
        else:
            if User_Input in new_dict_data_all[i]['results'][0]['ADDRESS'] or User_Input in new_dict_data_all[i]['results'][0]['ROAD_NAME'] or User_Input in new_dict_data_all[i]['results'][0]['POSTAL']:
                return new_dict_data_all[i]['results'][0]['LATITUDE'], new_dict_data_all[i]['results'][0]['LONGITUDE']


def Return_User_to_Node_Matching(userinput, nodesArray):
    minimum_dist = minimum = 728600

    print(userinput[0])
    print(userinput[1])
    user_location = (float(userinput[0]) , float(userinput[1]))
    print(user_location)
        
    for i in range(1,189):
        location = (nodesArray[i].latitude, nodesArray[i].longitude)
        
        distance = haversine(user_location, location, unit=Unit.METERS)
        if distance< minimum_dist:
            minimum_dist = distance
            minimum = i
            
    return minimum
    
#Calls and Defines the Node Array for path calculation
nodesArray = getNodesArray()



@map.route('/', methods=['GET', 'POST'])  # add url here
def read_map():
    
    
    #To pass back into the html Side
    data = {'startx': 1.43589365, 'starty': 103.8007271}

    if request.method == 'POST':
        print("executing the POST....")

        #Process User INput
        starting_location = request.form.get('myLocation')
        ending_location = request.form.get('mydestination')

        #Clean up the userInput 
        starting_location = starting_location.strip('\r\n      ')
        ending_location = ending_location.strip('\r\n      ')
        starting_location= starting_location.upper()
        ending_location = ending_location.upper()

        #Print the user input into the terminal
        print(starting_location)
        print(ending_location)

        #Checks if the user has inputed a valid location else prompt again
        if (Check_Valid_User_Input(starting_location)== None or Check_Valid_User_Input(ending_location)== None or Check_Valid_User_Input(starting_location) == Check_Valid_User_Input(ending_location)):
            print("Either User_Location Not Found or Similar PICKUP and DROPOFF point Selected, Please enter again :)")
            return render_template("map_page.html", data=data)
        
        else:
            print("User Location Found")
            #Print the lat and long of the selection
            print(Check_Valid_User_Input(starting_location))
            print(Check_Valid_User_Input(ending_location))
            
            print(Return_User_to_Node_Matching(Check_Valid_User_Input(starting_location), nodesArray))
            print(Return_User_to_Node_Matching(Check_Valid_User_Input(ending_location), nodesArray))
            
            Closest_Node_to_Pickup = Return_User_to_Node_Matching(Check_Valid_User_Input(starting_location), nodesArray)
            Closest_Node_to_Dropoff = Return_User_to_Node_Matching(Check_Valid_User_Input(starting_location), nodesArray)
            
            source_location_x = nodesArray[Closest_Node_to_Pickup].latitude
            source_location_y = nodesArray[Closest_Node_to_Pickup].longitude

            end_location_x = nodesArray[Closest_Node_to_Dropoff].latitude
            end_location_y = nodesArray[Closest_Node_to_Dropoff].longitude
            
            
            loc = distanceGraph.dijkstraAlgoGetPath(Closest_Node_to_Pickup, Closest_Node_to_Dropoff)[0]
            print(loc)
            
            data.update({
                
                'startx': source_location_x, 'starty': source_location_y, 'endx': end_location_x, 'endy':end_location_y
            
            })

            print(data)
            
            return render_template("map_page.html", data=data, lineCoord=loc)


    return render_template("map_page.html", data=data)