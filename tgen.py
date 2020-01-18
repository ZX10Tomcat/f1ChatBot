# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 21:25:47 2017

@author: Stergios
"""

from utils import integer_to_ordinal
from mappings import constuctor_mapping, driver_mapping, finishing_statuses
import random
from fb_buttons import create_image_or_video_fb_format
from datetime import datetime

def text_for_many_items(returned_list):
    text = []
    text = ", ".join(returned_list)
    k = text.rfind(',')
    if len(returned_list)>1:
        text = text[:k] + ' and' + text[k+1:]
    return text

def team_or_driver_text(team_or_driver, singular=True):
    if team_or_driver=='team':
        if singular:
            return 'team'
        else:
            return 'teams'
    else:
        if singular:
            return 'driver'
        else:
            return 'drivers'

def specific_position_text(name, position, gp_names, year_text, is_quali=False):
    race_info = " in " + gp_names + year_text
    if isinstance(position, int):
        if is_quali:
            text = name + " finished " + \
                integer_to_ordinal(position) + " in the qualifying" + race_info
        else:
            text = name + " finished " + \
                integer_to_ordinal(position) + " in the race" + race_info
    else:
        text = name + " retired in the race" + race_info
    return text

def specific_position_text_not_raced(name, gp_names, year_text, is_quali):
    race_info = " in " + gp_names + year_text
    if is_quali:
        text = name + " did not enter in the qualifying" + race_info
    else:
        text = name + " did not enter in the race" + race_info
    return text

def is_or_was(year, singular=True):
    if year=='current' or year==None:
        if singular:
            return 'is'
        else:
            return 'are'
    else:
        if singular:
            return 'was'
        else:
            return 'were'


def text_for_standings(returned_list, returned_positions, top_bottom, numeric, \
                    ordinal, driver, constructor, team_or_driver, year, returned_points):

    #TODO: add player points
    year_text = text_for_year(year)

    if returned_positions==[] and returned_points==[]:
        text = returned_list[0] + " did not take part in that championship."

    elif (driver!=None or constructor!=None):
        for i, pos in enumerate(returned_positions):
            try:
                returned_positions[i] = int(returned_positions[i])
            except Exception:
                pass

        text = returned_list[0] + " " + is_or_was(year) + " " +\
                    integer_to_ordinal(returned_positions[0]) +\
                    " in the " + team_or_driver_text(team_or_driver, singular=True) +\
                    "'s championship"
        if year=='current':
            text += " this year."
        else:
            text += " in " + str(year) + "."

    #Get specific number
    elif isinstance(ordinal, int):
        text = "The " + integer_to_ordinal(ordinal) + " " + team_or_driver_text(team_or_driver, singular=True) + \
                year_text + " " + is_or_was(year, singular=True) + " " + \
                text_for_many_items(returned_list) + "."

    #Get top N drivers-teams
    elif (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1

        if numeric==1:
            if year=='current':
                text = returned_list[0] + " won the " + team_or_driver_text(team_or_driver, singular=True) +\
                        "'s championship last year."
            else:
                text = returned_list[0] + " won the " + team_or_driver_text(team_or_driver, singular=True) +\
                        "'s championship in " + str(year) + "."
        else:
            text = "The first " + str(numeric) + " " + team_or_driver_text(team_or_driver, singular=False) + \
                    " in the championship " + year_text + " " +\
                    is_or_was(year, singular=False) + " " + \
                    text_for_many_items(returned_list) + "."

    #Get bottom N drivers-teams
    elif top_bottom=='bottom': #and isinstance(numeric, int)
        #This is for the question "which is the last team in the standings?"
        if numeric==None:
            numeric = 1
        if numeric==1:
            if year=='current':
                text = "The last " + team_or_driver_text(team_or_driver, singular=True) +\
                        "in championship last year was " + returned_list[0] + "."
            else:
                text = "The last " + team_or_driver_text(team_or_driver, singular=True) +\
                        "in " + str(year) + " championship was " + returned_list[0] + "."
        else:
            text = "The last " + str(numeric) + " " + team_or_driver_text(team_or_driver, singular=False) + \
                    " in the championship " + year_text + " " +\
                    is_or_was(year, singular=False) +\
                    " " + text_for_many_items(returned_list) + "."

    else:
        if year=='current':
            text = "Here are the current standings:\n" + \
                '\n'.join(returned_list)
        else:
            text = "Here are the standings for " + str(year) + ":\n" + \
                '\n'.join(returned_list)

    return text

def text_for_race_result(returned_list, returned_positions, gp_names, \
        top_bottom, numeric, ordinal, driver, constructor, team_or_driver, \
        is_quali=False, year='current'):
    if len(returned_list)>0 and len(returned_positions)>0:
        #Get specific driver-team
        #if top_bottom==None and numeric==None and ordinal==None and (driver!=None or constructor!=None):

        year_text = text_for_year(year)

        if (driver!=None or constructor!=None):
            #TODO: Add reason for retirement
            for i, pos in enumerate(returned_positions):
                try:
                    returned_positions[i] = int(returned_positions[i])
                except Exception:
                    pass

            if (team_or_driver=='team' or constructor!=None):
                text = "The first " + specific_position_text(returned_list[0], returned_positions[0], gp_names, year_text, is_quali) + \
                        " and the second " + specific_position_text(returned_list[1], returned_positions[1], gp_names, year_text, is_quali) + "."
            else:
                text = specific_position_text(returned_list[0], returned_positions[0], gp_names, year_text, is_quali) + "."

        #Get specific number
        elif isinstance(ordinal, int): #and top_bottom==None
            text = "The " + integer_to_ordinal(ordinal) + " " + team_or_driver_text(team_or_driver, singular=True) + \
                    " in " + gp_names + year_text + " was " + text_for_many_items(returned_list) + "."

        #Get top N drivers-teams
        elif (top_bottom=='top' or ordinal==1):
            if numeric==None:
                numeric = 1

            if numeric==1:
                if is_quali==True:
                    text = "The pole sitter in " + gp_names + year_text + \
                            " was " + text_for_many_items(returned_list) + "."
                else:
                    text = "The winner in " + gp_names + year_text + \
                            " was " + text_for_many_items(returned_list) + "."
            else:
                text = "The first " + str(numeric) + " " + team_or_driver_text(team_or_driver, singular=False) + \
                        " in " + gp_names + year_text + " were " + text_for_many_items(returned_list) + "."

        #Get bottom N drivers-teams
        elif top_bottom=='bottom': #and isinstance(numeric, int)
            #This is for the question "which is the last team in the standings?"
            if numeric==None:
                numeric = 1
            if numeric==1:
                text = "The last " + team_or_driver_text(team_or_driver, singular=True) \
                        + " in " + gp_names + year_text + " was " + \
                        text_for_many_items(returned_list) + "."
            else:
                text = "The last " + str(numeric) + " " + \
                        team_or_driver_text(team_or_driver, singular=False) + \
                        " in " + gp_names + year_text + " were " + \
                        text_for_many_items(returned_list) + "."

        else:
            if is_quali:
                text = ["Here is the final classification for the qualifying session in " + \
                        gp_names + year_text + ":"]
            else:
                text = ["Here is the final classification for the race in " + \
                        gp_names + year_text + ":"]


            #If the driver retired, show it in text
            for driver, pos in zip(returned_list, returned_positions):
                try:
                    pos = int(pos)
                except Exception:
                    pass
                if isinstance(pos, str) or isinstance(pos, unicode):
                    this_text = driver + " (" + pos + ")"
                else:
                    this_text = driver
                text.append(this_text)

    else:
        year_text = text_for_year(year)

        if (driver!=None or constructor!=None):
            if (team_or_driver=='team' or constructor!=None):
                text = "The first " + specific_position_text_not_raced(returned_list[0], gp_names, year_text, is_quali) + \
                        " and the second " + specific_position_text_not_raced(returned_list[1], gp_names, year_text, is_quali) + "."
            else:
                text = specific_position_text_not_raced(returned_list[0], gp_names, year_text, is_quali) + "."

    if isinstance(text, str) or isinstance(text, unicode):
        text = [text]

    return text


def text_for_quali_time(returned_constructors, returned_drivers, returned_times, gp_names, \
        top_bottom, numeric, ordinal, driver, constructor, team_or_driver, \
        year='current', returned_quali_phases=None):
    if len(returned_constructors)>0:

        year_text = text_for_year(year)

        if (driver!=None or constructor!=None):
            #TODO: Add reason for retirement
            if driver!=None:
                if returned_times[0] == None or returned_times[0] == 'None':
                    text = [returned_drivers[0] + " did not record a qualifying time in " + \
                            returned_quali_phases + " in " + gp_names + year_text + "."]
                else:
                    text = [returned_drivers[0] + "'s qualifying time in " + \
                            returned_quali_phases + " in " + gp_names + year_text +\
                            " was " + returned_times[0] + "."]
            elif (team_or_driver=='team' or constructor!=None):
                text = []
                for car_no in range(len(returned_constructors)):
                    if returned_times[car_no] == None or returned_times[car_no] == 'None':
                        text.append("The " + integer_to_ordinal(car_no+1) + \
                            " " + returned_constructors[car_no] + " (" + returned_drivers[car_no] + \
                            ") did not record a qualifying time in " + \
                            returned_quali_phases + " in " + gp_names + year_text + ".")
                    else:
                        text.append("The " + integer_to_ordinal(car_no+1) + \
                            " " + returned_constructors[car_no] + "'s (" + returned_drivers[car_no] + \
                            ") qualifying time in " + \
                            returned_quali_phases + " in " + gp_names + year_text +\
                            "was " + returned_times[car_no] + ".")

        #Get specific number
        elif isinstance(ordinal, int): #and top_bottom==None
            if ordinal==1:
                text = ["The fastest qualifying time in " + returned_quali_phases + \
                        " in " + gp_names + year_text + \
                        "was " + returned_times[0] + ".", "It was made by " + returned_drivers[0] +\
                        " (" + returned_constructors[0] + ")."]
            else:
                text = ["The " + integer_to_ordinal(ordinal) + " fastest qualifying time in " + \
                        returned_quali_phases + " in " + gp_names + year_text + \
                        "was " + returned_times[0] + ".", "It was made by " + returned_drivers[0] +\
                        " (" + returned_constructors[0] + ")."]

        #Get top N drivers-teams
        elif (top_bottom=='top' or ordinal==1):
            if numeric==None:
                numeric = 1

            if numeric==1:
                text = ["The fastest qualifying time in " + returned_quali_phases + \
                        " in " + gp_names + year_text + \
                        "was " + returned_times[0] + ".", "It was made by " + returned_drivers[0] +\
                        " (" + returned_constructors[0] + ")."]
            else:
                quali_times = text_for_quali_times(returned_constructors, returned_drivers, returned_times)
                text = ["Below are the top " + str(numeric) + " qualifying times " +\
                        "for " + returned_quali_phases + " in " + gp_names + year_text + "."]
                text = text + quali_times

        #Get bottom N drivers-teams
        elif top_bottom=='bottom': #and isinstance(numeric, int)
            #This is for the question "which is the last team in the standings?"
            if numeric==None:
                numeric = 1

            if numeric==1:
                text = ["The slowest qualifying time in " + returned_quali_phases + \
                        " in " + gp_names + year_text + \
                        "was " + returned_times[0] + ".", "It was made by " + returned_drivers[0] +\
                        " (" + returned_constructors[0] + ")."]
            else:
                quali_times = text_for_quali_times(returned_constructors, returned_drivers, returned_times)
                text = ["Below are the bottom " + str(numeric) + " qualifying times " +\
                        "for " + returned_quali_phases + " in " + gp_names + year_text + "."]
                text = text + quali_times

        else:
            quali_times = text_for_quali_times(returned_constructors, returned_drivers, returned_times)
            text = ["Below are the top 5 qualifying times " +\
                    "for " + returned_quali_phases + " in " + gp_names + year_text + "."]
            text = text + quali_times

    return text

def text_for_quali_times(returned_constructors, returned_drivers, returned_times):
    text = []
    for i in range(len(returned_constructors)):
        text.append(returned_drivers[i] + " (" + returned_constructors[i] + ") " +\
                    returned_times[i])

    return text

def text_for_retirement_reason(returned_reasons, \
                    gp_names, driver, constructor, year):
    if len(returned_reasons)>0:
        year_text = text_for_year(year)

        text = []
        if returned_reasons[0]=='no_retirement':
            if (driver!=None or constructor!=None):
                if driver!=None:
                    text.append(driver_mapping[driver] + " did not " +\
                                "retire in " + gp_names + year_text)
                else:
                    text.append("No " + constuctor_mapping[constructor] +\
                                " retired in " + gp_names + year_text)
        else:
            if (driver!=None or constructor!=None):
                if driver!=None:
                    text.append(driver_mapping[driver] + " retired due to " + \
                                    finishing_statuses[returned_reasons[0]] + " in " + gp_names + year_text)
                else:
                    if len(returned_reasons)>1:
                        for car_no in range(len(returned_reasons)):
                            text.append("The " + integer_to_ordinal(car_no+1) + \
                                    " " + constuctor_mapping[constructor] + " retired due to " + \
                                    finishing_statuses[returned_reasons[car_no]] + ".")

                    else:
                        text.append("A " + constuctor_mapping[constructor] +\
                                    " retired due to " + finishing_statuses[returned_reasons[0]] +\
                                    " in " + gp_names + year_text)
    return text

def text_for_retirees(returned_retirees, gp_names, year):
    returned_retirees = list(returned_retirees)
    if len(returned_retirees)>0:
        year_text = text_for_year(year)

        text = []
        text.append("There were " + str(len(returned_retirees)) + " retirements in " +\
                    gp_names + year_text)
        drivers_text = []
        for car in returned_retirees:
            drivers_text.append(driver_mapping[car[1]] + " (" + constuctor_mapping[car[0]] +\
                                ")")
#            text.append(driver_mapping[car[1]] + " (" + constuctor_mapping[car[0]] +\
#                    ") due to " + finishing_statuses[car[2]])
        drivers_text = ', '.join(drivers_text)
        text.append(drivers_text)
    return text


def text_for_pit_stops(returned_triplets, \
                    gp_names, driver, constructor, year):
    if len(returned_triplets)>0:
        year_text = text_for_year(year)

        if (driver!=None or constructor!=None):
            if constructor!=None:
                text = [constuctor_mapping[returned_triplets[1]] + " made " + str(returned_triplets[3]) +\
                        " pit-stops in " + gp_names + year_text + ".",
                        "The fastest one was completed in " + returned_triplets[2] +\
                        " seconds."]
            else:
                text = [driver_mapping[returned_triplets[0]] + " made " + str(returned_triplets[3]) +\
                        " pit-stops in " + gp_names + year_text + ".",
                        "The fastest one was completed in " + returned_triplets[2] +\
                        " seconds."]

        else:
            text = ["In total, " + str(returned_triplets[3]) +\
                    " pit-stops were made in " + gp_names + year_text + ".",
                    "The fastest one was completed in " + returned_triplets[2] +\
                    " seconds from " + driver_mapping[returned_triplets[0]] +\
                    " (" + constuctor_mapping[returned_triplets[1]] + ")."]
    return text

def no_such_race_text(lst, gp_name):
    if gp_name!=None:
        text = gp_name.title() + " in " + ' in '.join([str(i).title() for i in lst])
    else:
        text = "race in " + ' in '.join([str(i).title() for i in lst])
    return text

def text_for_year(year):
    if year == 'current' or year == None:
        r = random.random()
        if r>0.8:
            year_text = ' in the current year '
        else:
            year_text = ' in ' +datetime.now().strftime('%Y')
    else:
        year_text = ' in ' + str(year) + ' '

    return year_text

def text_for_drivers_of_team(returned_drivers, gp_name, constructor, \
                            mention_gp_name=False, year='current'):

    year_text = text_for_year(year)

    if len(returned_drivers)>0:
        if mention_gp_name:
            text = "The drivers of " + constuctor_mapping[constructor] + " in " + \
                    gp_name + year_text + " were " + text_for_many_items(returned_drivers) + "."
        else:
            text = "The drivers of " + constuctor_mapping[constructor] + \
                    " are " + text_for_many_items(returned_drivers) + "."
    return text

def text_for_team_of_driver(returned_constructors, gp_name, driver, \
                            mention_gp_name=False, year='current'):
    
    year_text = text_for_year(year)

    if len(returned_constructors)>0:
        if mention_gp_name:
            text = "The team of " + driver_mapping[driver] + " in " + \
                    gp_name + year_text + " was " + text_for_many_items(returned_constructors) + "."
        else:
            text = "The team of " + driver_mapping[driver] + \
                    " is " + text_for_many_items(returned_constructors) + "."
    return text

def text_for_next_race_schedule(gp_name, race_date, race_time):
    #TODO: Count days since today e.g. "The next race in 12 days from now..."
    alternatives = ["The next race in " + gp_name + " is scheduled for " + \
                    race_date + " (" + race_time + ")."]

    return random.choice(alternatives)

#text_for_aggregate_stats('silverstone', 'UK', None, None, 2015, 'top', 1, None, 'alonso', 'ferrari', None, None, 5)
def text_for_aggregate_stats(gp_name, circuit_name, locality, country, \
                    year, top_bottom, numeric, ordinal, driver, \
                    constructor, team_or_driver, podium, metric_value):

    print (top_bottom, numeric, ordinal, podium)

    if year==None:
        year_text = ''
    else:
        year_text = text_for_year(year)

    #Get top N drivers
    if (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1
    elif podium!=None:
        top_bottom='top'
        numeric = 3

    text = ""
    if driver!=None and constructor!=None:
        text += driver_mapping[driver] + ", driving for " + \
                constuctor_mapping[constructor] + ","
    elif driver!=None and constructor==None:
        text += driver_mapping[driver]
    elif driver==None and constructor!=None:
        text += constuctor_mapping[constructor]

    #Get specific number
    if isinstance(ordinal, int):
        text += " has finished " + integer_to_ordinal(ordinal)

    #Get top N drivers-teams
    elif (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1

        if numeric==1:
            text += " has won"
        else:
            text += " has finished in the top " + str(numeric) + " positions"

    #Get bottom N drivers-teams
    elif top_bottom=='bottom':
        if numeric==None:
            numeric = 1
        if numeric==1:
            text += " has finished last"
        else:
            text += " has finished in the last " + str(numeric) + " positions"

    time_or_times = ' time' if metric_value==1 else ' times'
    text += " " + str(metric_value) + time_or_times + " "

    text += text_for_circuits(gp_name, circuit_name, locality, country)

    text += year_text

    return text

def text_for_circuits(gp_name, circuit_name, locality, country):
    text = ''
    lst = [gp_name, circuit_name, locality, country]
    lst = [i for i in lst if i!=None]
    if len(lst)==1:
        text += " in " + lst[0]
    elif len(lst)>1:
        text += " in " + " in ".join(lst)

    text = text.strip()
    return text
#text_for_appearances_stats(None, None, None, None, None, 'alonso', None, None, 274)
def text_for_appearances_stats(gp_name, circuit_name, locality, country, \
                    year, driver, constructor, metric_value):

    if year==None:
        year_text = ''
    else:
        year_text = text_for_year(year)

    text = ""
    if driver!=None and constructor!=None:
        text += driver_mapping[driver] + ", driving for " + \
                constuctor_mapping[constructor] + ","
    elif driver!=None and constructor==None:
        text += driver_mapping[driver]
    elif driver==None and constructor!=None:
        text += constuctor_mapping[constructor]

    text += " has entered"

    race_or_races = ' race' if metric_value==1 else ' races'
    text += " " + str(metric_value) + race_or_races + " "

    text += text_for_circuits(gp_name, circuit_name, locality, country)

    text += year_text

    return text

def text_driver_not_in_team(driver, constructor):
    text = driver_mapping[driver] + " was not driving for " + \
            constuctor_mapping[constructor] + " at that time."
    return text

def connect_teams_or_drivers(zipmap, team_or_driver='driver'):
    if team_or_driver=='driver':
        val = text_for_many_items([driver_mapping[k] for k, v in zipmap])
    else:
        val = text_for_many_items([constuctor_mapping[k] for k, v in zipmap])
    return val

def text_for_most_aggregate_stats(gp_name, circuit_name, locality, country, year, \
                        team_or_driver, ordinal, podium, \
                        numeric, top_bottom, driver, \
                        constructor, metric_value):

    #TODO: Make proper text if None
    if metric_value[0][0]==None:
        text = "This combination has no wins!"
        return text

    if year==None:
        year_text = ''
    else:
        year_text = text_for_year(year)

    #Get top N drivers
    if (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1
    elif podium!=None:
        top_bottom = 'top'
        numeric = 3

    if team_or_driver==None:
        team_or_driver = 'driver'

    is_or_are = 'is' if len(metric_value)==1 else 'are'
    has_or_have = 'has' if len(metric_value)==1 else 'have'
    singular = True if len(metric_value)==1 else False

    text = ''
    text += connect_teams_or_drivers(metric_value, team_or_driver) + " " + \
            is_or_are + " the " + team_or_driver_text(team_or_driver, singular)

    #Get specific number
    if isinstance(ordinal, int):
        text += " with the most " + integer_to_ordinal(ordinal) + " positions"

    #Get top N drivers-teams
    elif (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1

        if numeric==1:
            text += " with the most wins"
        else:
            text += " that " + has_or_have + " finished in the top " + \
                    str(numeric) + " positions " + "the most times"


    if constructor!=None:
        text += " with a " + constuctor_mapping[constructor]
    if driver!=None:
        text += " with " + driver_mapping[driver] + " as a driver"

    #Add text for circuits
    lst = [gp_name, circuit_name, locality, country]
    print (lst)
    lst = [i.title() for i in lst if i!=None]
    if len(lst)==1:
        text += " in " + lst[0]
    elif len(lst)>1:
        text += " in " + " in ".join(lst)

    text += year_text + " (" + str(int(metric_value[0][1])) + ")."

    return text

def text_for_aggregate_quali_stats(gp_name, circuit_name, locality, country, \
                    year, top_bottom, numeric, ordinal, driver, \
                    constructor, team_or_driver, pole, metric_value):

    if year==None:
        year_text = ''
    else:
        year_text = text_for_year(year)

    #Get top N drivers
    if (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1
    elif pole!=None:
        top_bottom='top'
        numeric = 1

    text = ""
    if driver!=None and constructor!=None:
        text += driver_mapping[driver] + ", driving for " + \
                constuctor_mapping[constructor] + ","
    elif driver!=None and constructor==None:
        text += driver_mapping[driver]
    elif driver==None and constructor!=None:
        text += constuctor_mapping[constructor]

    #Get specific number
    if isinstance(ordinal, int):
        text += " has qualified " + integer_to_ordinal(ordinal)

    #Get top N drivers-teams
    elif (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1

        if numeric==1:
            text += " has taken the pole position"
        else:
            text += " has qualified in the top " + str(numeric) + " positions"

    #Get bottom N drivers-teams
    elif top_bottom=='bottom':
        if numeric==None:
            numeric = 1
        if numeric==1:
            text += " has qualified last"
        else:
            text += " has qualified in the last " + str(numeric) + " positions"

    time_or_times = ' time' if metric_value==1 else ' times'
    text += " " + str(metric_value) + time_or_times

    #Add text for circuits
    lst = [gp_name, circuit_name, locality, country]
    print (lst)
    lst = [i for i in lst if i!=None]
    if len(lst)==1:
        text += " in " + lst[0]
    elif len(lst)>1:
        text += " in " + " in ".join(lst)

    text += year_text

    return text

def text_for_most_aggregate_quali_stats(gp_name, circuit_name, locality, country, year, \
                        team_or_driver, ordinal, pole, \
                        numeric, top_bottom, driver, \
                        constructor, metric_value):

    #TODO: Make proper text if None
    if metric_value[0][0]==None:
        text = "This combination has no pole positions!"
        return text

    if year==None:
        year_text = ''
    else:
        year_text = text_for_year(year)

    #Get top N drivers
    if (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1
    elif pole!=None:
        top_bottom = 'top'
        numeric = 1

    if team_or_driver==None:
        team_or_driver = 'driver'

    is_or_are = 'is' if len(metric_value)==1 else 'are'
    has_or_have = 'has' if len(metric_value)==1 else 'have'
    singular = True if len(metric_value)==1 else False

    text = ''
    text += connect_teams_or_drivers(metric_value, team_or_driver) + " " + \
            is_or_are + " the " + team_or_driver_text(team_or_driver, singular)

    #Get specific number
    if isinstance(ordinal, int):
        text += " with the most " + integer_to_ordinal(ordinal) + " positions in qualifying"

    #Get top N drivers-teams
    elif (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1

        if numeric==1:
            text += " with the most pole positions"
        else:
            text += " that " + has_or_have + " qualified in the top " + \
                    str(numeric) + " positions " + "the most times"


    if constructor!=None:
        text += " with a " + constuctor_mapping[constructor]
    if driver!=None:
        text += " with " + driver_mapping[driver] + " as a driver"

    #Add text for circuits
    lst = [gp_name, circuit_name, locality, country]
    print (lst)
    lst = [i.title() for i in lst if i!=None]
    if len(lst)==1:
        text += " in " + lst[0]
    elif len(lst)>1:
        text += " in " + " in ".join(lst)

    text += year_text + " (" + str(int(metric_value[0][1])) + ")."

    return text

def text_for_championship_stats(top_bottom, numeric, ordinal, driver, \
                    constructor, metric_value, years):

    #Get top N drivers
    if (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1

    text = ""
    if driver!=None and constructor!=None:
        text += driver_mapping[driver] + ", driving for " + \
                constuctor_mapping[constructor] + ","
    elif driver!=None and constructor==None:
        text += driver_mapping[driver]
    elif driver==None and constructor!=None:
        text += constuctor_mapping[constructor]

    #Get specific number
    if isinstance(ordinal, int):
        text += " has finished " + integer_to_ordinal(ordinal) + " in the championship"

    #Get top N drivers-teams
    elif (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1

        if numeric==1:
            text += " has won the championship"
        else:
            text += " has finished in the top " + str(numeric) + " positions of the championship"

    time_or_times = ' time' if metric_value==1 else ' times'
    text += " " + str(metric_value) + time_or_times + "."

    #Add text for years
    if len(years)>0:
        years_text = "This happened in " + text_for_many_items(years) + "."
    else:
        years_text = ''

    return [text, years_text]

def text_for_most_championship_stats(team_or_driver, ordinal, \
                        numeric, top_bottom, driver, constructor, \
                        metric_value):
    #TODO: Make proper text if None
    if metric_value[0][0]==None:
        text = "This combination has no championships!"
        return text

    #Get top N drivers
    if (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1

    if team_or_driver==None:
        team_or_driver = 'driver'

    is_or_are = 'is' if len(metric_value)==1 else 'are'
    has_or_have = 'has' if len(metric_value)==1 else 'have'
    singular = True if len(metric_value)==1 else False

    text = ''
    text += connect_teams_or_drivers(metric_value, team_or_driver) + " " + \
            is_or_are + " the " + team_or_driver_text(team_or_driver, singular)

    #Get specific number
    if isinstance(ordinal, int):
        text += " with the most " + integer_to_ordinal(ordinal) + " positions in the championship"

    #Get top N drivers-teams
    elif (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1

        if numeric==1:
            text += " with the most championships"
        else:
            text += " that " + has_or_have + " finished in the top " + \
                    str(numeric) + " positions " +\
                    "of the championship the most times"


    if constructor!=None:
        text += " with a " + constuctor_mapping[constructor]
    if driver!=None:
        text += " with " + driver_mapping[driver] + " as a driver"

    #Add text for times
    time_or_times = ' time' if metric_value[0][1]==1 else ' times'
    text += " (" + str(int(metric_value[0][1])) + time_or_times + ")."

    return text

#TODO: This should be updated after every race.
def text_for_most_appearance_stats(team_or_driver):

    if team_or_driver=='driver' or team_or_driver==None:
        text = "The driver with the most race starts is Rubens Barrichello with 326 entries."
    else:
        text = "The team with the most race starts is Ferrari with 932 entries" +\
                " (till the end of 2016 season)."

    return text

def text_for_fastest_lap(returned_constructors, returned_times, returned_drivers, \
                    gp_names, year, returned_lap_rounds):
    year_text = text_for_year(year)

    text = ["The fastest lap in " + gp_names + year_text + " was made by " +\
            returned_drivers + " (" + returned_constructors + ") on round " +\
            str(returned_lap_rounds) + ".",
            "The laptime was " + returned_times + "."]

    return text

def text_for_social_media(driver, constructor, tw_account):
    if tw_account=='no_account':
        if driver!=None:
            text = driver_mapping[driver] + " has no official Twitter account."
        elif constructor!=None:
            text = constuctor_mapping[constructor] + " has no official Twitter account."
    elif tw_account=='not_current':
        text = "I only know the twitter accounts of current drivers and teams."
    else:
        if driver!=None:
            text = driver_mapping[driver] + "'s official Twitter account is " + tw_account
        elif constructor!=None:
            text = constuctor_mapping[constructor] + "'s official Twitter account is " + tw_account

    return text

def text_for_local_comparison(triplette, position, team_or_driver):
    text = ''
    if triplette[0]==None:
        text += "they both have an equal number of "
        if position==1:
            text += "wins"
        else:
            text += integer_to_ordinal(position) + " positions"
        text += " (" + str(triplette[1]) + "), "
    else:
        if position==1:
            if team_or_driver=='driver':
                text += "he has more "
            else:
                text += "the team has more "
            text += "wins"
        else:
            if team_or_driver=='driver':
                text += "but " + driver_mapping[triplette[0]] + " has more "
            else:
                text += "but " + constuctor_mapping[triplette[0]] + " has more "
            text += integer_to_ordinal(position) + " positions"
        text += " (" + str(triplette[1]) + " compared to " + str(triplette[2]) + ")."
    return text


def text_for_driver_or_team_comparison(best, results, team_or_driver):
    if best == None:
        text = "None of the " + team_or_driver + "s has any podiums, so I cannot " +\
                "compare them."
        return text

    text = ''
    if team_or_driver=='team':
        text += constuctor_mapping[best]
    else:
        text += driver_mapping[best]

    text += " is better since "
    for i, local_results in enumerate(results):
        text += text_for_local_comparison(local_results, i+1, team_or_driver)

    return text

def text_for_best_driver_or_team(team_or_driver):
    if team_or_driver=='driver':
        text = ["The best driver ever is Fernando Alonso!", "Vamos!"]
    else:
        text = ["Well... Ferrari is the most successful team!", "Forza Ferrari!"]

    return text

def text_for_god():
    alternatives = ['My God is Fernando Alonso. I\'m sorry Lewis!',
                    'I only believe in Fernando Alonso. The greatest ever!']

    text = random.choice(alternatives)
    alo_image = create_image_or_video_fb_format('image', 'http://oi64.tinypic.com/16hryw3.jpg')

    return [text, alo_image]

#text_for_teammate(gp_name, circuit_name, locality, country, 'current', driver, returned_driver)
def text_for_teammate(gp_name, circuit_name, locality, country, \
                    year, driver, returned_driver):

    text = driver_mapping[driver] + "'s teammate"
    circuit_text = text_for_circuits(gp_name, circuit_name, locality, country)

    if year==None and circuit_text=='':
        text += ' is '
    else:
        if circuit_text!='':
            text += ' ' + circuit_text
        if year!=None:
            year_text = text_for_year(year)
            text += ' ' + year_text.strip()
        text += ' was '

    text += returned_driver + '.'

    return text

def driver_not_racing(gp_name, circuit_name, locality, country, \
                    year, driver):
    text = driver_mapping[driver]
    circuit_text = text_for_circuits(gp_name, circuit_name, locality, country)

    if year==None and circuit_text=='':
        text += ' is not racing now.'
    else:
        text += ' was not racing'
        if circuit_text!='':
            text += ' ' + circuit_text
        if year!=None:
            year_text = text_for_year(year)
            text += ' ' + year_text.strip()
        text += "."

    return text

def text_for_driver_or_team_info(driver, constructor, url, \
                                nationality, birthday):
    text = []
    if driver!=None:
        a_or_an = 'an' if nationality[0].lower() in ['a','e','u','i','o'] else 'a'
        text.append(driver_mapping[driver] + " is " + a_or_an + " " + \
                    nationality + " driver.")
        text.append("He was born on " + str(birthday) + ".")
    else:
        a_or_an = 'an' if nationality[0].lower() in ['a','e','u','i','o'] else 'a'
        text.append(constuctor_mapping[constructor] + " is " + a_or_an + " " + \
                    nationality + " team.")

    text.append("You can find more info here:")
    text.append(url)

    return text

#Source: http://f1.wikia.com/wiki/Flag_system
def text_for_flags(flag_colours_shapes):
    text = None
    if flag_colours_shapes==None or flag_colours_shapes==[]:
        text = None
    elif set(['yellow', 'red']) <= set(flag_colours_shapes) or \
        set(['yellow', 'striped']) <= set(flag_colours_shapes) or \
        set(['red', 'striped']) <= set(flag_colours_shapes):
        text = "The yellow and red striped flag indicates a slippery track, due to oil, water or loose debris."
    elif set(['black', 'orange']) <= set(flag_colours_shapes) or \
        set(['black', 'circle']) <= set(flag_colours_shapes) or \
        set(['orange', 'circle']) <= set(flag_colours_shapes):
        text = "The black with orange circle flag indicates that a car is damaged and must pit immediately."
    elif set(['black', 'white']) <= set(flag_colours_shapes) or \
        set(['black', 'half']) <= set(flag_colours_shapes) or \
        set(['white', 'half']) <= set(flag_colours_shapes):
        text = "The half black, half white flag indicates warns a driver for unsportsmanlike behaviour."
    elif set(['double', 'yellow']) <= set(flag_colours_shapes):
        text = "The double yellow flag inform drivers that marshals are working on or near to the track."
    elif flag_colours_shapes[0] == 'chequered':
        text = "The chequered flag indicates that a session has been completed."
    elif flag_colours_shapes[0] == 'yellow':
        text = "The yellow flag indicates a hazard on or near the track."
    elif flag_colours_shapes[0] == 'green':
        text = "The green flag indicates that normal racing conditions apply."
    elif flag_colours_shapes[0] == 'red':
        text = "The red flag indicates that a session has been stopped."
    elif flag_colours_shapes[0] == 'blue':
        text = "The blue flag indicates that the driver in front must let faster cars behind pass."
    elif flag_colours_shapes[0] == 'black':
        text = "The black flag indicates that a driver is disqualified (usually accompanied by the driver's number)."
    elif flag_colours_shapes[0] == 'white':
        text = "The white flag indicates that that a slow moving car is ahead."

    return text

def no_season_review(year):
    if year == None:
        text = "Which year's review would you like to see?"
    elif year<1950 or year>2017:
        text = "Formula 1 has been held between 1950 and 2017. Please select one of these years."

    return text

def season_review(year, url):
    resp = {}
    resp['type']='button'
    resp['header'] = "You can read more about the " + str(year) + " season here:"
    resp['buttons_list'] = [('web_url', str(year) + ' season review', url)]
    return resp