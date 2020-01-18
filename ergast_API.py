from bs4 import BeautifulSoup
import urllib3
import pandas as pd
import string
import requests
from mappings import replace_characters, driver_mapping, constuctor_mapping

from datetime import datetime
import time
import logging

def url_to_soup(url):
    if 'wikipedia' not in url:
        http = urllib3.PoolManager()
        response = http.request('GET', url)
        soup = BeautifulSoup(response.data, 'html.parser')

    else:
        response = requests.get(url).text
        soup = BeautifulSoup(response, 'html.parser')


    return soup

def yearly_race_schedule(year=2008):
    soup = url_to_soup('http://ergast.com/api/f1/' + str(year))
    
    races_list = []                    
    for race_row in soup.find('mrdata').find('racetable').find_all('race'):
        race_round = race_row['round']
        race_name = race_row.racename.text
        circuit_name = race_row.circuitname.text
        race_city = race_row.locality.text
        race_country = race_row.country.text
        race_date = race_row.date.text

        try:
            race_time = race_row.time.text
        except AttributeError:
            race_time = ''

        this_race = {'race_round' : race_round,
                     'race_name' : race_name,
                     'circuit_name' : circuit_name,
                     'race_city' : race_city,
                     'race_country' : race_country,
                     'race_date' : race_date,
                     'race_time' : race_time}

        races_list.append(this_race)

    results_df = pd.DataFrame.from_dict(races_list)
    results_df['gp_name'] = results_df.race_name.apply(lambda x: x.lower().split()[0] + ' gp')
    results_df.replace(replace_characters, regex=True, inplace=True)
    return results_df

def race_results(year=2008, gp_round=5):
    try:
        soup = url_to_soup('http://ergast.com/api/f1/' + str(year) + '/' + str(gp_round) + '/results')
        print (soup.prettify())
        results_list = []
        for result_row in soup.find('resultslist').find_all('result'):
            driver_Id = result_row.driver['driverid']
            driver_position = result_row['position']
            driver_position_text = result_row['positiontext']
            constructor_Id = result_row.constructor['constructorid']
            status = result_row.status.text.lower()

            this_result = {'driver_Id' : driver_Id,
                           'driver_position' : driver_position,
                          'driver_position_text' : driver_position_text,
                          'constructor_Id' : constructor_Id,
                          'status' : status}

            results_list.append(this_result)

        results_df = pd.DataFrame.from_dict(results_list)
        return results_df
    except (AttributeError, KeyError) as ex:        
        logging.exception("message")        
        return "data_NA"

def quali_results(year=2008, gp_round=5):

    try:
        soup = url_to_soup('http://ergast.com/api/f1/' + str(year) + '/' + str(gp_round) + '/qualifying')

        results_list = []
        for result_row in soup.find('qualifyinglist').find_all('qualifyingresult'):
            driver_Id = result_row.driver['driverid']
            driver_position = result_row['position']
            constructor_Id = result_row.constructor['constructorid']
            try:
                q1_time = result_row.Q1.text
            except Exception:
                q1_time = None
            try:
                q2_time = result_row.Q2.text
            except Exception:
                q2_time = None
            try:
                q3_time = result_row.Q3.text
            except Exception:
                q3_time = None

            this_result = {'driver_Id' : driver_Id,
                           'driver_position' : driver_position,
                          'constructor_Id' : constructor_Id,
                          'q1': q1_time,
                          'q2': q2_time,
                          'q3': q3_time}

            results_list.append(this_result)

        results_df = pd.DataFrame.from_dict(results_list)
        return results_df

    except Exception:
        return "data_NA"

def pit_stop_results(year=2008, gp_round=5):

    try:
        soup = url_to_soup('http://ergast.com/api/f1/' + str(year) + '/' + str(gp_round) + '/pitstops?limit=1000&offset=0')

        this_race_results = race_results(year, gp_round)
        this_race_results.drop(['driver_position', 'driver_position_text', 'status'], axis=1, inplace=True)

        results_list = []
        for result_row in soup.find('pitstopslist').find_all('pitstop'):
            driver_Id = result_row['driverid']
            duration = result_row['duration']

            this_result = {'driver_Id' : driver_Id,
                           'duration' : duration}

            results_list.append(this_result)

        results_df = pd.DataFrame.from_dict(results_list)

        #This is needed to get the team information
        results_df = pd.merge(results_df, this_race_results, how='left', on='driver_Id')
        return results_df

    except Exception:
        return "data_NA"

def fastest_lap(year=2008, gp_round=5):
    try:
        soup = url_to_soup('http://ergast.com/api/f1/' + str(year) + '/' + str(gp_round) + '/results')

        fastest_lap_time, driver_Id, constructor_Id, fastest_lap_time_round = None, None, None, None
        for result_row in soup.find('resultslist').find_all('result'):
            this_fastest_lap = result_row.find('fastestlap')
            if int(this_fastest_lap['rank'])==1:
                fastest_lap_time = this_fastest_lap.find('time').text
                fastest_lap_time_round = this_fastest_lap['lap']
                driver_Id = result_row.driver['driverid']
                constructor_Id = result_row.constructor['constructorid']
                break

        return fastest_lap_time, driver_Id, constructor_Id, fastest_lap_time_round
    except Exception:
        return "data_NA", None, None, None

def year_standings(year, team_or_driver):
    if year==None:
        year = 'current'
    if team_or_driver==None:
        team_or_driver = 'driver'

    try:
        if team_or_driver=='driver':
            soup = url_to_soup('http://ergast.com/api/f1/' + str(year) + '/driverStandings')

            results_list = []
            for result_row in soup.find('standingslist').find_all('driverstanding'):
                driver_Id = result_row.driver['driverid']
                driver_position = result_row['position']
                constructor_Id = result_row.constructor['constructorid']
                points = result_row['points']

                this_result = {'driver_Id' : driver_Id,
                               'driver_position' : driver_position,
                              'constructor_Id' : constructor_Id,
                              'points': points}

                results_list.append(this_result)

        else:
            soup = url_to_soup('http://ergast.com/api/f1/' + str(year) + '/constructorStandings')

            results_list = []
            for result_row in soup.find('standingslist').find_all('constructorstanding'):
                constructor_position = result_row['position']
                constructor_Id = result_row.constructor['constructorid']
                points = result_row['points']

                this_result = {'constructor_position' : constructor_position,
                              'constructor_Id' : constructor_Id,
                              'points': points}

                results_list.append(this_result)

        results_df = pd.DataFrame.from_dict(results_list)
        return results_df, year

    except Exception:
        return "data_NA", year

def drivers_of_team_in_race(year=2008, gp_round=5, constructor_name = 'ferrari'):
    try:
        soup = url_to_soup('http://ergast.com/api/f1/' + str(year) + '/' + str(gp_round) + \
                    '/constructors/' + constructor_name + '/drivers')

        results_list = []
        for result_row in soup.find('drivertable').find_all('driver'):
            driver_Id = result_row['driverid']
            this_result = {'driver_Id' : driver_Id}
            results_list.append(this_result)

        if results_list==[]:
            results_df = 'data_NA'
        else:
            results_df = pd.DataFrame.from_dict(results_list)

    except Exception:
        results_df = 'data_NA'

    return results_df

def team_of_driver_in_race(year=2008, gp_round=5, driver_name = 'alonso'):
    try:
        soup = url_to_soup('http://ergast.com/api/f1/' + str(year) + '/' + str(gp_round) + \
                    '/drivers/' + driver_name + '/constructors')

        results_list = []
        for result_row in soup.find('ConstructorTable').find_all('Constructor'):
            constructor_Id = result_row['constructorId']
            this_result = {'constructor_Id' : constructor_Id}
            results_list.append(this_result)

        if results_list==[]:
            results_df = 'data_NA'
        else:
            results_df = pd.DataFrame.from_dict(results_list)
    except Exception:
        results_df = 'data_NA'

    return results_df

def find_this_race(gp_name, circuit_name, locality, country, race_schedule):
    lst = [gp_name, circuit_name, locality, country]

    df_columns_to_check = ['gp_name', 'circuit_name', 'race_city', 'race_country']
    df_columns_to_check = [j for i, j in enumerate(df_columns_to_check) if lst[i]!=None]
    lst = [i for i in lst if i!=None]

    this_race = race_schedule
    for col_no in range(len(df_columns_to_check)):
        this_race = this_race[this_race[df_columns_to_check[col_no]].str.lower()==lst[col_no].lower()]

    if this_race.empty==False:
        return this_race
    else:
        return None

def next_specific_race(gp_name, circuit_name, locality, country, race_schedule):
    today = datetime.fromtimestamp(time.mktime(time.gmtime())).strftime('%Y-%m-%d')
    race_schedule = race_schedule[race_schedule.race_date>=today]

    if gp_name==None and circuit_name==None and locality==None and country==None \
        and race_schedule.shape[0]>0:
        this_race = race_schedule.iloc[0]
    else:
        lst = [gp_name, circuit_name, locality, country]

        df_columns_to_check = ['gp_name', 'circuit_name', 'race_city', 'race_country']
        df_columns_to_check = [j for i, j in enumerate(df_columns_to_check) if lst[i]!=None]
        lst = [i for i in lst if i!=None]

        this_race = race_schedule
        for col_no in range(len(df_columns_to_check)):
            this_race = this_race[this_race[df_columns_to_check[col_no]].str.lower()==lst[col_no]]

        #Change Dataframe to Series
        this_race = this_race.T.squeeze()

    if this_race.empty==False:
        race_round = int(this_race['race_round'])
        gp_name = this_race['circuit_name']#.values[0]
        race_date = this_race['race_date']#.values[0]
        race_date = datetime.strptime(race_date, '%Y-%m-%d').strftime('%d-%b-%Y')
        race_time = this_race['race_time'][:-4]#this_race['race_time'].values[0][:-4]
        return race_round, gp_name, race_date, race_time
    else:
        return None, None, None, None


def get_race_round_and_gp_names(year, gp_name, circuit_name, locality, country):

    if year==None:
        year = 'current'

    race_schedule = yearly_race_schedule(year)
    this_race = find_this_race(gp_name, circuit_name, locality, country, race_schedule)
    if gp_name==None and circuit_name==None and locality==None and country==None:
        this_race = this_race.tail(1)
    gp_names = []

    if isinstance(this_race, pd.DataFrame):
        if this_race.shape[0]>1:
            race_round = [int(i) for i in this_race['race_round']]
            gp_names = [i for i in this_race['circuit_name']]
        else:
            race_round = [int(this_race['race_round'])]
            gp_names = list(this_race['circuit_name'].values)
    else:
        race_round = [0]

    return year, race_round, gp_names




def race_result(gp_name, circuit_name, locality, country, year, top_bottom=None, numeric=None, ordinal=None, driver_name=None, constructor_name=None, team_or_driver=None):

    year, race_round, gp_names = get_race_round_and_gp_names(year, gp_name, circuit_name, locality, country)

    returned_drivers = []
    returned_constructors = []
    returned_positions = []
    raw_constructors = []
    raw_drivers = []

    if race_round!=[0]:
        for race in race_round:
            results = race_results(year, race)

            if isinstance(results, str) and results=='data_NA':
                return 'data_NA', None, None, None, None, None, None

            #Get specific driver or constructor
            #if top_bottom==None and numeric==None and ordinal==None and (driver_name!=None or constructor_name!=None):
            if driver_name!=None or constructor_name!=None:
                if constructor_name!=None:
                    this_positions = list(results[results.constructor_Id==constructor_name]['driver_position_text'].values)
                    this_drivers = []
                    this_constructors = [constructor_name] * len(this_positions)
                else:
                    this_positions = list(results[results.driver_Id==driver_name]['driver_position_text'].values)
                    this_drivers = [driver_name]
                    this_constructors = []
                    #TODO: change text to 'Retired' for example

            #Get specific number
            elif isinstance(ordinal, int): #and top_bottom==None
                if results.shape[0]<ordinal:
                    return results.shape[0], None, None, None, None, None, None

                if team_or_driver=='team':
                    this_constructors = [results.iloc[ordinal-1]['constructor_Id']]
                    this_drivers = []
                    this_positions = [results.iloc[ordinal-1]['driver_position_text']]
                else:
                    this_constructors = []
                    this_drivers = [results.iloc[ordinal-1]['driver_Id']]
                    this_positions = [results.iloc[ordinal-1]['driver_position_text']]

            #Get top N drivers
            elif (top_bottom=='top' or ordinal==1): #and isinstance(numeric, int)
                #This is for the question "who was the winner in that race?"
                if numeric==None:
                    numeric = 1

                if results.shape[0]<numeric:
                    return results.shape[0], None, None, None, None, None, None

                if team_or_driver=='team':
                    this_constructors = list(results.head(numeric)['constructor_Id'])
                    this_drivers = []
                    this_positions = list(results.head(numeric)['driver_position_text'])
                else:
                    this_constructors = []
                    this_drivers = list(results.head(numeric)['driver_Id'])
                    this_positions = list(results.head(numeric)['driver_position_text'])

            #Get bottom N teams
            elif top_bottom=='bottom': #and isinstance(numeric, int)
                #This is for the question "which is the last team in the standings?"
                if numeric==None:
                    numeric = 1

                if results.shape[0]<numeric:
                    return results.shape[0], None, None, None, None, None, None

                if team_or_driver=='team':
                    this_constructors = list(results.tail(numeric)['constructor_Id'])
                    this_drivers = []
                    this_positions = list(results.tail(numeric)['driver_position_text'])
                else:
                    this_constructors = []
                    this_drivers = list(results.tail(numeric)['driver_Id'])
                    this_positions = list(results.tail(numeric)['driver_position_text'])

            else:
                if team_or_driver=='team':
                    this_constructors = list(results['constructor_Id'])
                    this_drivers = []
                    this_positions = list(results['driver_position_text'].values)
                else:
                    this_constructors = []
                    this_drivers = list(results['driver_Id'])
                    this_positions = list(results['driver_position_text'].values)

            returned_constructors.append([constuctor_mapping[i] for i in this_constructors])
            returned_drivers.append([driver_mapping[i] for i in this_drivers])
            returned_positions.append(this_positions)
            raw_constructors.append([i for i in this_constructors])
            raw_drivers.append([i for i in this_drivers])

    return returned_constructors, returned_drivers, returned_positions, gp_names, \
            raw_constructors, raw_drivers, year

def quali_result(gp_name, circuit_name, locality, country, year, top_bottom=None, numeric=None, ordinal=None, driver_name=None, constructor_name=None, team_or_driver=None):

    year, race_round, gp_names = get_race_round_and_gp_names(year, gp_name, circuit_name, locality, country)

    returned_drivers = []
    returned_constructors = []
    returned_positions = []
    raw_constructors = []
    raw_drivers = []

    if race_round!=[0]:
        for race in race_round:
            results = quali_results(year, race)

            if isinstance(results, str) and results=='data_NA':
                return 'data_NA', None, None, None, None, None, None

            #Get specific driver or constructor
            #if top_bottom==None and numeric==None and ordinal==None and (driver_name!=None or constructor_name!=None):
            if driver_name!=None or constructor_name!=None:
                if constructor_name!=None:
                    this_positions = list(results[results.constructor_Id==constructor_name]['driver_position'].values)
                    this_drivers = []
                    this_constructors = [constructor_name] * len(this_positions)
                else:
                    this_positions = list(results[results.driver_Id==driver_name]['driver_position'].values)
                    this_drivers = [driver_name]
                    this_constructors = []
                    #TODO: change text to 'Retired' for example

            #Get specific number
            elif isinstance(ordinal, int): #and top_bottom==None
                if results.shape[0]<ordinal:
                    return results.shape[0], None, None, None, None, None, None
                if team_or_driver=='team':
                    this_constructors = [results.iloc[ordinal-1]['constructor_Id']]
                    this_drivers = []
                    this_positions = [results.iloc[ordinal-1]['constructor_Id']]
                else:
                    this_constructors = []
                    this_drivers = [results.iloc[ordinal-1]['driver_Id']]
                    this_positions = [results.iloc[ordinal-1]['driver_position']]

            #Get top N drivers
            elif (top_bottom=='top' or ordinal==1): #and isinstance(numeric, int)
                #This is for the question "who was the winner in that race?"
                if numeric==None:
                    numeric = 1

                if results.shape[0]<numeric:
                    return results.shape[0], None, None, None, None, None, None

                if team_or_driver=='team':
                    this_constructors = list(results.head(numeric)['constructor_Id'])
                    this_drivers = []
                    this_positions = list(results.head(numeric)['driver_position'])
                else:
                    this_constructors = []
                    this_drivers = list(results.head(numeric)['driver_Id'])
                    this_positions = list(results.head(numeric)['driver_position'])

            #Get bottom N teams
            elif top_bottom=='bottom': #and isinstance(numeric, int)
                #This is for the question "which is the last team in the standings?"
                if numeric==None:
                    numeric = 1

                if results.shape[0]<numeric:
                    return results.shape[0], None, None, None, None, None, None

                if team_or_driver=='team':
                    this_constructors = list(results.tail(numeric)['constructor_Id'])
                    this_drivers = []
                    this_positions = list(results.tail(numeric)['driver_position'])
                else:
                    this_constructors = []
                    this_drivers = list(results.tail(numeric)['driver_Id'])
                    this_positions = list(results.tail(numeric)['driver_position'])

            else:
                if team_or_driver=='team':
                    this_constructors = list(results['constructor_Id'])
                    this_drivers = []
                    this_positions = list(results['driver_position'])
                else:
                    this_constructors = []
                    this_drivers = list(results['driver_Id'])
                    this_positions = list(results['driver_position'])

            returned_constructors.append([constuctor_mapping[i] for i in this_constructors])
            returned_drivers.append([driver_mapping[i] for i in this_drivers])
            returned_positions.append(this_positions)
            raw_constructors.append([i for i in this_constructors])
            raw_drivers.append([i for i in this_drivers])

    return returned_constructors, returned_drivers, returned_positions, gp_names, \
            raw_constructors, raw_drivers, year

def determine_last_quali_phase(results):
    if results['q3'].iloc[0]!=None:
        return 'q3'
    elif results['q2'].iloc[0]!=None:
        return 'q2'
    elif results['q1'].iloc[0]!=None:
        return 'q1'

def quali_times(gp_name, circuit_name, locality, country, year, \
                top_bottom=None, numeric=None, ordinal=None, \
                driver_name=None, constructor_name=None, \
                team_or_driver=None, init_quali_phase=None):

    year, race_round, gp_names = get_race_round_and_gp_names(year, gp_name, circuit_name, locality, country)

    returned_drivers = []
    returned_constructors = []
    returned_times = []
    raw_constructors = []
    raw_drivers = []
    returned_quali_phases = []

    if race_round!=[0]:
        for race in race_round:
            results = quali_results(year, race)

            if isinstance(results, str) and results=='data_NA':
                return 'data_NA', None, None, None, None, None, None, None

            if init_quali_phase==None:
                quali_phase = determine_last_quali_phase(results)
            else:
                quali_phase = init_quali_phase

            quali_phases = ['q1', 'q2', 'q3']
            quali_phases_to_drop = [i for i in quali_phases if i!=quali_phase]
            results.drop(quali_phases_to_drop, axis=1, inplace=True)
            results.columns = ['constructor_Id', 'driver_Id', 'driver_position', 'time']
            results.sort_values('time', inplace=True)
            results['time'] = results['time'].astype(str)
            #results = results[(results['time']!='None') & (results['time']!='')]

            if results.shape[0]==results[(results['time']=='None') | (results['time']=='')].shape[0] and init_quali_phase!=None:
                return 'q_NA', None, None, None, None, None, None, None

            #Get specific driver or constructor
            #if top_bottom==None and numeric==None and ordinal==None and (driver_name!=None or constructor_name!=None):
            if driver_name!=None or constructor_name!=None:
                if driver_name!=None:
                    this_drivers = [driver_name]
                    this_constructors = list(results[results.driver_Id==driver_name]['constructor_Id'].values)
                    this_times = list(results[results.driver_Id==driver_name]['time'].values)
                else:
                    this_drivers = list(results[results.constructor_Id==constructor_name]['driver_Id'].values)
                    this_constructors = [constructor_name] * len(this_drivers)
                    this_times = list(results[results.constructor_Id==constructor_name]['time'].values)


            elif isinstance(ordinal, int): #and top_bottom==None
                results = results[(results['time']!='None') & (results['time']!='')]
                if results.shape[0]<ordinal:
                    return results.shape[0], None, None, None, None, None, None, None

                this_constructors = [results.iloc[ordinal-1]['constructor_Id']]
                this_drivers = [results.iloc[ordinal-1]['driver_Id']]
                this_times = [results.iloc[ordinal-1]['time']]

            #Get top N drivers
            elif (top_bottom=='top' or ordinal==1): #and isinstance(numeric, int)
                #This is for the question "who was the winner in that race?"
                if numeric==None:
                    numeric = 1

                results = results[(results['time']!='None') & (results['time']!='')]

                if results.shape[0]<numeric:
                    return results.shape[0], None, None, None, None, None, None, None

                this_constructors = list(results.head(numeric)['constructor_Id'])
                this_drivers = list(results.head(numeric)['driver_Id'])
                this_times = list(results.head(numeric)['time'])

            #Get bottom N teams
            elif top_bottom=='bottom': #and isinstance(numeric, int)
                #This is for the question "which is the last team in the standings?"
                if numeric==None:
                    numeric = 1

                results = results[(results['time']!='None') & (results['time']!='')]

                if results.shape[0]<numeric:
                    return results.shape[0], None, None, None, None, None, None, None

                this_constructors = list(results.tail(numeric)['constructor_Id'])
                this_times = list(results.tail(numeric)['time'])
                this_drivers = list(results.tail(numeric)['driver_Id'])

            else:
                this_constructors = list(results.head(5)['constructor_Id'])
                this_drivers = list(results.head(5)['driver_Id'])
                this_times = list(results.head(5)['time'])

            returned_constructors.append([constuctor_mapping[i] for i in this_constructors])
            returned_drivers.append([driver_mapping[i] for i in this_drivers])
            returned_times.append(this_times)
            raw_constructors.append([i for i in this_constructors])
            raw_drivers.append([i for i in this_drivers])
            returned_quali_phases.append(quali_phase)

    return returned_constructors, returned_drivers, returned_times, gp_names, \
            raw_constructors, raw_drivers, year, returned_quali_phases

def clean_pit_stop_times(duration):
    if len(duration[0])==9:
        this_duration = str(duration[0]).translate(None, string.punctuation)
        return this_duration[:2] + '.' + this_duration[2:]
    else:
        return duration

def pit_stop_times(gp_name, circuit_name, locality, country, year, \
                driver_name=None, constructor_name=None):

    year, race_round, gp_names = get_race_round_and_gp_names(year, gp_name, circuit_name, locality, country)

    returned_triplets = []

    if race_round!=[0]:
        for race in race_round:
            results = pit_stop_results(year, race)

            if isinstance(results, str) and results=='data_NA':
                return 'data_NA', None, None

            results['duration'] = results[['duration']].apply(lambda x: \
                                        clean_pit_stop_times(x), axis=1)
            results.sort_values('duration', inplace=True)

            #Get specific driver or constructor
            if driver_name!=None or constructor_name!=None:
                if constructor_name!=None:
                    results = results[results.constructor_Id==constructor_name]
                    this_drivers = results.iloc[0]['driver_Id']
                    this_constructors = constructor_name
                    this_duration = results.iloc[0]['duration']
                    this_count = results.shape[0]
                    this_triplet = ([this_drivers, this_constructors, this_duration, this_count])
                else:
                    results = results[results.driver_Id==driver_name]
                    this_drivers = driver_name
                    this_constructors = results.iloc[0]['constructor_Id']
                    this_duration = results.iloc[0]['duration']
                    this_count = results.shape[0]
                    this_triplet = ([this_drivers, this_constructors, this_duration, this_count])

            #Get top N drivers
            else:
                this_drivers = results.iloc[0]['driver_Id']
                this_constructors = results.iloc[0]['constructor_Id']
                this_duration = results.iloc[0]['duration']
                this_count = results.shape[0]
                this_triplet = ([this_drivers, this_constructors, this_duration, this_count])


            returned_triplets.append(this_triplet)

    return returned_triplets, year, gp_names

def retirement_reason(gp_name, circuit_name, locality, country, year, \
                driver_name=None, constructor_name=None):

    year, race_round, gp_names = get_race_round_and_gp_names(year, gp_name, circuit_name, locality, country)

    returned_reasons = []

    if race_round!=[0]:
        for race in race_round:
            results = race_results(year, race)

            if isinstance(results, str) and results=='data_NA':
                return 'data_NA'

            results = results[(results['status'].str.lower()!='finished') & \
                                (~(results['status'].str.lower().str.contains('lap')))]

            if results.shape[0]==0:
                return 'no_retirement'

            #Get specific driver or constructor
            if driver_name!=None or constructor_name!=None:
                if constructor_name!=None:
                    results = results[results.constructor_Id==constructor_name]
                    if results.shape[0]==0:
                        this_reasons  = ['no_retirement']
                    else:
                        this_reasons = list(results['status'].values)
                else:
                    results = results[results.driver_Id==driver_name]
                    if results.shape[0]==0:
                        this_reasons  = ['no_retirement']
                    else:
                        this_reasons = list(results['status'].values)

            returned_reasons.append(this_reasons)

    return returned_reasons, year, gp_names

def retirees(gp_name, circuit_name, locality, country, year):

    year, race_round, gp_names = get_race_round_and_gp_names(year, gp_name, circuit_name, locality, country)

    returned_retirees = []

    if race_round!=[0]:
        for race in race_round:
            results = race_results(year, race)

            if isinstance(results, str) and results=='data_NA':
                return 'data_NA'

            results = results[(results['status'].str.lower()!='finished') & \
                                (~(results['status'].str.lower().str.contains('lap')))]

            if results.shape[0]==0:
                return 'no_retirement'

            this_retirees = zip(results.constructor_Id.values, results.driver_Id.values, results.status.values)
            returned_retirees.append(this_retirees)

    return returned_retirees, year, gp_names


def get_circuitRef(gp_name, circuit_name, locality, country):

    races = pd.read_csv('races.csv')
    lst = [gp_name, circuit_name, locality, country]
    df_columns_to_check = ['gp_name', 'circuit_name', 'locality', 'country']
    df_columns_to_check = [j for i, j in enumerate(df_columns_to_check) if lst[i]!=None]
    lst = [i for i in lst if i!=None]

    for col_no in range(len(df_columns_to_check)):
        if df_columns_to_check[col_no]=='gp_name':
            lst[col_no] = lst[col_no].replace('gp', 'grand prix')
        races = races[races[df_columns_to_check[col_no]].str.lower()==lst[col_no].lower()]
    circuitRefs = list(races['circuitRef'].drop_duplicates())

    return circuitRefs

def append_to_elements_in_list(lst, appendage):
    lst = [i + appendage for i in lst]
    return lst

#compare_drivers_or_teams(['bottas', 'sainz'], None)
#compare_drivers_or_teams(['alonso', 'hamilton'], None)
#compare_drivers_or_teams(['max_verstappen', 'kubica'], None)
#compare_drivers_or_teams(None, ['ferrari', 'mclaren'])
#compare_drivers_or_teams(None, ['maserati', 'ligier'])
#driver_names = ['', 'bottas']
def find_comparison_winner(lst, df):
    df = df[df.index.isin(lst)]
    if df.shape[0]>0:
        if df.shape[0]==1:
            return (df.index[0], df.iloc[0].values[0], 0)
        elif df.iloc[0].values[0] != df.iloc[1].values[0]:
            return (df.index[0], df.iloc[0].values[0], df.iloc[1].values[0])
        else:
            return (None, df.iloc[0].values[0], df.iloc[1].values[0])
    else:
        return (None, 0, 0)


def compare_drivers_or_teams(driver_names = None, constructor_names = None):
    results = []

    for i in range(1, 4): #Check only for podium positions
        first_url = 'http://ergast.com/api/f1/results/' + str(i) + '?limit=1000'
        soup = url_to_soup(first_url)
        df = results_most_aggregate_stats_soup_to_pd(soup)

        if driver_names!=None:
            df = df.groupby('driver_Id').count()
            df.sort_values('constructor_Id', ascending=False, inplace=True)
        else:
            df = df.groupby('constructor_Id').count()
            df.sort_values('driver_Id', ascending=False, inplace=True)

        df.columns = ['value']
        lst = constructor_names if driver_names==None else driver_names
        comparison_winner = find_comparison_winner(lst, df)
        results.append(comparison_winner)
        if comparison_winner[0]!=None:
            break

    try:
        best = [i[0] for i in results if i[0]!=None][0]
    except Exception:
        best = None
    return best, results



#aggregate_stats(None, None, None, None, None, None, None, 1, 'alonso', None, None)
#aggregate_stats(None, None, None, None, None, None, None, 1, 'alonso', 'renault', None)
#aggregate_stats(None, None, None, None, 2015, 'top', 1, None, None, 'ferrari', None)
#aggregate_stats(None, None, None, 'italy', None, 'top', 1, None, 'hamilton', None, None)
def aggregate_stats(gp_name, circuit_name, locality, country, year, top_bottom=None, \
                    numeric=None, ordinal=None, driver_name=None, \
                    constructor_name=None, podium=None):

    #Get top N drivers
    if (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1
    elif podium!=None:
        top_bottom = 'top'
        numeric = 3

    urls = ['http://ergast.com/api/f1']
    if year!=None:
        appendage = '/' + str(year)
        urls = append_to_elements_in_list(urls, appendage)
    if gp_name!=None or circuit_name!=None or locality!=None or country!=None:
        circuitRefs = get_circuitRef(gp_name, circuit_name, locality, country)
        urls = [url + '/circuits/' + circ for circ in circuitRefs for url in urls]
    if driver_name!=None:
        appendage = '/drivers/' + driver_name
        urls = append_to_elements_in_list(urls, appendage)
    if constructor_name!=None:
        appendage = '/constructors/' + constructor_name
        urls = append_to_elements_in_list(urls, appendage)
    if ordinal!=None:
        appendage = '/results/' + str(ordinal)
        urls = append_to_elements_in_list(urls, appendage)
    elif numeric!=None:
        if top_bottom=='top':
            urls = [url + '/results/' + str(num) for num in range(1, numeric+1) for url in urls]
        else:
            if numeric==None:
                numeric = 1
            appendage = '/results/' + str(numeric)
            urls = append_to_elements_in_list(urls, appendage)


    appendage = '?limit=1'
    urls = append_to_elements_in_list(urls, appendage)

    print (urls)

    #urls = [u'http://ergast.com/api/f1/drivers/raikkonen?limit=1000']

    metric_value = 0
    for url in urls:
        soup = url_to_soup(url)
        #print ("soup:" + str(soup.find('mrdata')))
        #total = soup.find('MRData')['total']
        metric_value += int(soup.find('mrdata')['total'])
        #metric_value += len(soup.find('RaceTable').find_all('Race'))

    return metric_value

def results_most_aggregate_stats_soup_to_pd(soup):
    try:
        races = []
        for race in soup.find('racetable').find_all('race'):
            this_race = {}
            this_race['driver_id'] = race.find('driver')['driverid']
            this_race['constructor_id'] = race.find('constructor')['constructorid']
            races.append(this_race)

        df = pd.DataFrame.from_dict(races)
    except Exception:
        df = None
    return df

#most_aggregate_stats(None, None, None, 'australia', None, 'driver', None, None, 3, 'top')
#print most_aggregate_stats(None, None, None, None, None, 'team', None, None, 5, 'top')
#print most_aggregate_stats(None, None, None, None, None, None, None, 'podium', None, None)
#most_aggregate_stats(None, None, None, None, None, 'driver', None, None, None, 'top', None, 'mercedes')
def most_aggregate_stats(gp_name, circuit_name, locality, country, year, \
                        team_or_driver=None, ordinal=None, podium=None, \
                        numeric=None, top_bottom=None, driver=None, constructor=None):

    #Get top N drivers
    if (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1
    elif podium!=None:
        top_bottom = 'top'
        numeric = 3

    urls = ['http://ergast.com/api/f1']
    if year!=None:
        appendage = '/' + str(year)
        urls = append_to_elements_in_list(urls, appendage)
    if gp_name!=None or circuit_name!=None or locality!=None or country!=None:
        circuitRefs = get_circuitRef(gp_name, circuit_name, locality, country)
        urls = [url + '/circuits/' + circ for circ in circuitRefs for url in urls]
    if driver!=None:
        appendage = '/drivers/' + driver
        urls = append_to_elements_in_list(urls, appendage)
    if constructor!=None:
        appendage = '/constructors/' + constructor
        urls = append_to_elements_in_list(urls, appendage)
    if ordinal!=None:
        appendage = '/results/' + str(ordinal)
        urls = append_to_elements_in_list(urls, appendage)
    elif numeric!=None:
        if top_bottom=='top':
            urls = [url + '/results/' + str(num) for num in range(1, numeric+1) for url in urls]
        else:
            if numeric==None:
                numeric = 1
            appendage = '/results/' + str(numeric)
            urls = append_to_elements_in_list(urls, appendage)


    appendage = '?limit=1000'
    urls = append_to_elements_in_list(urls, appendage)

    print (urls)

    init_df = pd.DataFrame()
    for i, url in enumerate(urls):
        soup = url_to_soup(url)

        #TODO: Handle case if there are no results - now if gives an error.
        #E.g. Who has the most wins with a red bull in the british gp?
        df = results_most_aggregate_stats_soup_to_pd(soup)

        print (i, url)

        if not(isinstance(df, pd.DataFrame)) or df.empty:# or df == None:
            continue

        if team_or_driver=='driver' or team_or_driver==None:
            df = df.groupby('driver_id').count()
            df.sort_values('constructor_id', ascending=False, inplace=True)
        else:
            df = df.groupby('constructor_id').count()
            df.sort_values('driver_id', ascending=False, inplace=True)

        #print df.head()

        if i==0:
            init_df = df
        else:
            init_df = pd.merge(init_df, df, left_index=True, right_index=True, how='outer')
            init_df = init_df.sum(axis=1)
            init_df = pd.DataFrame(init_df)

            if team_or_driver=='driver' or team_or_driver==None:
                init_df.columns = ['constructor_id']
            else:
                init_df.columns = ['driver_id']

        #print init_df.head()
        #print "==============="

    if init_df.empty:
        return None, None

    if team_or_driver=='driver' or team_or_driver==None:
        init_df.sort_values('constructor_id', ascending=False, inplace=True)
        print (init_df.head())
        init_df = init_df[init_df.constructor_id==int(init_df.max())]
    else:
        init_df.sort_values('driver_id', ascending=False, inplace=True)
        print (init_df.head())
        init_df = init_df[init_df.driver_id==int(init_df.max())]

    print (init_df.head())

    return [tuple(x) for x in init_df.to_records()]

    #return init_df.index[0], init_df.iloc[0].values[0]

#aggregate_quali_stats(None, None, None, None, None, None, None, 1, 'alonso', None, None)
#aggregate_quali_stats(None, None, None, None, None, None, None, 1, 'alonso', 'renault', None)
#aggregate_quali_stats(None, None, None, None, 2015, 'top', 1, None, None, 'ferrari', None)
#aggregate_quali_stats(None, None, None, 'italy', None, 'top', 1, None, 'hamilton', None, None)
def aggregate_quali_stats(gp_name, circuit_name, locality, country, year, top_bottom=None, \
                    numeric=None, ordinal=None, driver_name=None, \
                    constructor_name=None, pole=None):

    #Get top N drivers
    if (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1
    elif pole!=None:
        top_bottom = 'top'
        numeric = 1

    urls = ['http://ergast.com/api/f1']
    if year!=None:
        appendage = '/' + str(year)
        urls = append_to_elements_in_list(urls, appendage)
    if gp_name!=None or circuit_name!=None or locality!=None or country!=None:
        circuitRefs = get_circuitRef(gp_name, circuit_name, locality, country)
        urls = [url + '/circuits/' + circ for circ in circuitRefs for url in urls]
    if driver_name!=None:
        appendage = '/drivers/' + driver_name
        urls = append_to_elements_in_list(urls, appendage)
    if constructor_name!=None:
        appendage = '/constructors/' + constructor_name
        urls = append_to_elements_in_list(urls, appendage)
    if ordinal!=None:
        appendage = '/grid/' + str(ordinal)
        urls = append_to_elements_in_list(urls, appendage)
    elif numeric!=None:
        if top_bottom=='top':
            urls = [url + '/grid/' + str(num) for num in range(1, numeric+1) for url in urls]
        else:
            if numeric==None:
                numeric = 1
            appendage = '/grid/' + str(numeric)
            urls = append_to_elements_in_list(urls, appendage)


    appendage = '/qualifying?limit=1'
    urls = append_to_elements_in_list(urls, appendage)

    print (urls)

    metric_value = 0
    for url in urls:
        soup = url_to_soup(url)
        metric_value += int(soup.find('mrdata')['total'])
        #metric_value += len(soup.find('RaceTable').find_all('Race'))

    return metric_value

#most_aggregate_quali_stats(None, None, None, 'italy', None, 'driver', None, None, None, 'top')
#most_aggregate_quali_stats(None, None, 'monza', None, None, 'driver', None, 'pole', None, 'top', None, 'ferrari')
#most_aggregate_quali_stats(None, None, None, None, None, 'team', None, None, 5, 'top')
#most_aggregate_quali_stats(None, None, None, 'belgium', None, 'driver', None, None, None, 'top', None, None)
#most_aggregate_quali_stats(None, None, None, 'spain', None, 'driver', None, None, None, 'top', None, None)
def most_aggregate_quali_stats(gp_name, circuit_name, locality, country, year, \
                        team_or_driver=None, ordinal=None, pole=None, \
                        numeric=None, top_bottom=None, driver=None, constructor=None):

    #Get top N drivers
    if (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1
    elif pole!=None:
        top_bottom = 'top'
        numeric = 1

    urls = ['http://ergast.com/api/f1']
    if year!=None:
        appendage = '/' + str(year)
        urls = append_to_elements_in_list(urls, appendage)
    if gp_name!=None or circuit_name!=None or locality!=None or country!=None:
        circuitRefs = get_circuitRef(gp_name, circuit_name, locality, country)
        urls = [url + '/circuits/' + circ for circ in circuitRefs for url in urls]
    if driver!=None:
        appendage = '/drivers/' + driver
        urls = append_to_elements_in_list(urls, appendage)
    if constructor!=None:
        appendage = '/constructors/' + constructor
        urls = append_to_elements_in_list(urls, appendage)
    if ordinal!=None:
        appendage = '/grid/' + str(ordinal)
        urls = append_to_elements_in_list(urls, appendage)
    elif numeric!=None:
        if top_bottom=='top':
            urls = [url + '/grid/' + str(num) for num in range(1, numeric+1) for url in urls]
        else:
            if numeric==None:
                numeric = 1
            appendage = '/grid/' + str(numeric)
            urls = append_to_elements_in_list(urls, appendage)

    appendage = '/qualifying?limit=1000'
    urls = append_to_elements_in_list(urls, appendage)

    print (urls)

    init_df = pd.DataFrame()
    for i, url in enumerate(urls):
        soup = url_to_soup(url)

        #TODO: Handle case if there are no results - now if gives an error.
        #E.g. Who has the most wins with a red bull in the british gp?
        df = results_most_aggregate_stats_soup_to_pd(soup)

        print (i, url)

        if not(isinstance(df, pd.DataFrame)) or df.empty:# or df == None:
            continue

        if team_or_driver=='driver' or team_or_driver==None:
            df = df.groupby('driver_Id').count()
            df.sort_values('constructor_Id', ascending=False, inplace=True)
        else:
            df = df.groupby('constructor_Id').count()
            df.sort_values('driver_Id', ascending=False, inplace=True)

        if i==0:
            init_df = df
        else:
            init_df = pd.merge(init_df, df, left_index=True, right_index=True, how='outer')
            init_df = init_df.sum(axis=1)
            init_df = pd.DataFrame(init_df)

            if team_or_driver=='driver' or team_or_driver==None:
                init_df.columns = ['constructor_Id']
            else:
                init_df.columns = ['driver_Id']

        #print init_df
        #print "==============="

    if init_df.empty:
        return None, None

    if team_or_driver=='driver' or team_or_driver==None:
        init_df.sort_values('constructor_Id', ascending=False, inplace=True)
        print (init_df.head())
        init_df = init_df[init_df.constructor_Id==int(init_df.max())]
    else:
        init_df.sort_values('driver_Id', ascending=False, inplace=True)
        print (init_df.head())
        init_df = init_df[init_df.driver_Id==int(init_df.max())]

    print (init_df.head(10))

#    return init_df.index[0], init_df.iloc[0].values[0]
    return [tuple(x) for x in init_df.to_records()]

#appearances_stats(None, None, None, None, None, 'alonso', None)
#appearances_stats(None, None, None, None, None, None, 'ferrari')
#appearances_stats(None, None, None, 'italy', None, 'alonso', None)
#appearances_stats(None, None, None, None, None, 'alonso', 'ferrari')
def appearances_stats(gp_name, circuit_name, locality, country, year, \
                    driver_name=None, constructor_name=None):

    urls = ['http://ergast.com/api/f1']
    if year!=None:
        appendage = '/' + str(year)
        urls = append_to_elements_in_list(urls, appendage)
    if gp_name!=None or circuit_name!=None or locality!=None or country!=None:
        circuitRefs = get_circuitRef(gp_name, circuit_name, locality, country)
        urls = [url + '/circuits/' + circ for circ in circuitRefs for url in urls]
    if driver_name!=None:
        appendage = '/drivers/' + driver_name
        urls = append_to_elements_in_list(urls, appendage)
    if constructor_name!=None:
        appendage = '/constructors/' + constructor_name
        urls = append_to_elements_in_list(urls, appendage)

    appendage = '/results?limit=1'
    urls = append_to_elements_in_list(urls, appendage)

    print (urls)

    metric_value = 0
    for url in urls:
        soup = url_to_soup(url)
        metric_value += int(soup.find('MRData')['total'])

    return metric_value

#most_appearance_stats(None, None, None, 'italy', None, 'team', None, None)
#most_appearance_stats(None, None, None, None, None, 'team', None, None)
#most_appearance_stats(None, None, None, None, None, None, None, None)
#most_appearance_stats(None, None, None, None, None, 'driver', None, None)

#TODO: API cannot return so many data.. Only in batches
#Consider creating a CSV file.
def most_appearance_stats(gp_name, circuit_name, locality, country, year, \
                        team_or_driver=None, driver=None, constructor=None):

    urls = ['http://ergast.com/api/f1']
    if year!=None:
        appendage = '/' + str(year)
        urls = append_to_elements_in_list(urls, appendage)
    if gp_name!=None or circuit_name!=None or locality!=None or country!=None:
        circuitRefs = get_circuitRef(gp_name, circuit_name, locality, country)
        urls = [url + '/circuits/' + circ for circ in circuitRefs for url in urls]
    if driver!=None:
        appendage = '/drivers/' + driver
        urls = append_to_elements_in_list(urls, appendage)
    if constructor!=None:
        appendage = '/constructors/' + constructor
        urls = append_to_elements_in_list(urls, appendage)

    appendage = '/results?limit=25000'
    urls = append_to_elements_in_list(urls, appendage)

    print (urls)

    init_df = pd.DataFrame()
    for i, url in enumerate(urls):
        soup = url_to_soup(url)

        #TODO: Handle case if there are no results - now if gives an error.
        #E.g. Who has the most wins with a red bull in the british gp?
        df = results_most_aggregate_stats_soup_to_pd(soup)

        print (i, url)

        if not(isinstance(df, pd.DataFrame)) or df.empty:# or df == None:
            continue

        if team_or_driver=='driver' or team_or_driver==None:
            df = df.groupby('driver_Id').count()
            df.sort_values('constructor_Id', ascending=False, inplace=True)
        else:
            df = df.groupby('constructor_Id').count()
            df.sort_values('driver_Id', ascending=False, inplace=True)

        if i==0:
            init_df = df
        else:
            init_df = pd.merge(init_df, df, left_index=True, right_index=True, how='outer')
            init_df = init_df.sum(axis=1)
            init_df = pd.DataFrame(init_df)

            if team_or_driver=='driver' or team_or_driver==None:
                init_df.columns = ['constructor_Id']
            else:
                init_df.columns = ['driver_Id']

    if init_df.empty:
        return None, None

    if team_or_driver=='driver' or team_or_driver==None:
        init_df.sort_values('constructor_Id', ascending=False, inplace=True)
        print (init_df.head())
        init_df = init_df[init_df.constructor_Id==int(init_df.max())]
    else:
        init_df.sort_values('driver_Id', ascending=False, inplace=True)
        print (init_df.head())
        init_df = init_df[init_df.driver_Id==int(init_df.max())]

    print (init_df.head())

    return [tuple(x) for x in init_df.to_records()]

#championship_results('top', None, None, 'vettel', 'red_bull')
#championship_results('top', None, None, 'raikkonen', None)
#championship_results(None, None, 1, 'hamilton', None)
#championship_results('top', 3, None, None, 'ferrari')
def championship_results(top_bottom=None, numeric=None, ordinal=None, driver_name=None, \
                    constructor_name=None):

    #Get top N drivers
    if (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1

    urls = ['http://ergast.com/api/f1']
    if driver_name!=None:
        appendage = '/drivers/' + driver_name
        urls = append_to_elements_in_list(urls, appendage)
    elif constructor_name!=None:
        appendage = '/constructors/' + constructor_name
        urls = append_to_elements_in_list(urls, appendage)
    if ordinal!=None:
        if driver_name!=None:
            #urls = ['http://ergast.com/api/f1/driverStandings']
            appendage = '/driverStandings/' + str(ordinal)
            urls = append_to_elements_in_list(urls, appendage)
        elif constructor_name!=None:
            appendage = '/constructorStandings/' + str(ordinal)
            urls = append_to_elements_in_list(urls, appendage)
    elif numeric!=None:
        if top_bottom=='top':
            if driver_name!=None:
                urls = [url + '/driverStandings/' + str(num) for num in range(1, numeric+1) for url in urls]
            elif constructor_name!=None:
                urls = [url + '/constructorStandings/' + str(num) for num in range(1, numeric+1) for url in urls]
        else:
            if numeric==None:
                numeric = 1
            if driver_name!=None:
                appendage = '/driverStandings/' + str(numeric)
                urls = append_to_elements_in_list(urls, appendage)
            elif constructor_name!=None:
                appendage = '/constructorStandings/' + str(numeric)
                urls = append_to_elements_in_list(urls, appendage)


    appendage = '?limit=1000'
    urls = append_to_elements_in_list(urls, appendage)

    print (urls)

    metric_value = 0
    years = []
    for url in urls:
        df = standings_results_soup_to_pd(url)

        if not(isinstance(df, pd.DataFrame)) or df.empty:# or df == None:
            continue

        #How many championships does Alonso have with Ferrari
        if df.shape[0]>0 and driver_name!=None and constructor_name!=None:
            df = df[df.constructor_Id == constructor_name]

        metric_value += df.shape[0]
        years.extend(df.season.values)

    if years!=[]:
        years = list(set(years))
        years.sort()

    return metric_value, years

def standings_results_soup_to_pd(url):
    try:
        soup = url_to_soup(url)
        races = []
        if 'driverStandings' in url:
            for race in soup.find_all('StandingsList'):
                this_race = {}
                this_race['driver_Id'] = race.find('Driver')['driverId']
                this_race['constructor_Id'] = race.find('Constructor')['constructorId']
                this_race['season'] = race['season']
                races.append(this_race)
        else:
            for race in soup.find_all('StandingsList'):
                this_race = {}
                this_race['constructor_Id'] = race.find('Constructor')['constructorId']
                this_race['season'] = race['season']
                races.append(this_race)

        df = pd.DataFrame.from_dict(races)
    except Exception:
        df = None
    return df

#most_championship_results('top', None, None, 'raikkonen', None, 'team')
#most_championship_results('top', None, None, 'raikkonen', None, 'team')
#most_championship_results('top', None, None, None, None, 'team')
#most_championship_results('top', 3, None, None, None, 'team')
def most_championship_results(top_bottom=None, numeric=None, ordinal=None,
                              driver_name=None, constructor_name=None, team_or_driver=None):

    #Get top N drivers
    if (top_bottom=='top' or ordinal==1):
        if numeric==None:
            numeric = 1

    urls = ['http://ergast.com/api/f1']
    if ordinal!=None:
        if team_or_driver=='driver' or team_or_driver==None or driver_name!=None:
            appendage = '/driverStandings/' + str(ordinal)
            urls = append_to_elements_in_list(urls, appendage)
        else:
            appendage = '/constructorStandings/' + str(ordinal)
            urls = append_to_elements_in_list(urls, appendage)
    elif numeric!=None:
        if top_bottom=='top':
            if team_or_driver=='driver' or team_or_driver==None or driver_name!=None:
                urls = [url + '/driverStandings/' + str(num) for num in range(1, numeric+1) for url in urls]
            else:
                urls = [url + '/constructorStandings/' + str(num) for num in range(1, numeric+1) for url in urls]
        else:
            if numeric==None:
                numeric = 1
            if team_or_driver=='driver' or team_or_driver==None or driver_name!=None:
                appendage = '/driverStandings/' + str(numeric)
                urls = append_to_elements_in_list(urls, appendage)
            else:
                appendage = '/constructorStandings/' + str(numeric)
                urls = append_to_elements_in_list(urls, appendage)


    appendage = '?limit=1000'
    urls = append_to_elements_in_list(urls, appendage)

    print (urls)

    init_df = pd.DataFrame()
    for i, url in enumerate(urls):

        df = standings_results_soup_to_pd(url)

        if not(isinstance(df, pd.DataFrame)) or df.empty:# or df == None:
            continue

        if team_or_driver=='driver' or team_or_driver==None or driver_name!=None:
            if constructor_name!=None:
                df = df[df.constructor_Id==constructor_name]
            elif driver_name!=None:
                df = df[df.driver_Id==driver_name]

            if driver_name!=None:
                df = df.groupby('constructor_Id').count()
                df.sort_values('driver_Id', ascending=False, inplace=True)
                df.drop('season', axis=1, inplace=True)
            else:
                df = df.groupby('driver_Id').count()
                df.sort_values('constructor_Id', ascending=False, inplace=True)
                df.drop('season', axis=1, inplace=True)
        else:
            df = df.groupby('constructor_Id').count()
            df.sort_values('season', ascending=False, inplace=True)
            df.columns = ['driver_Id']
            #df.drop('season', axis=1, inplace=True)

        #print df.head()
        #print "==============="

        if i==0:
            init_df = df
        else:
            init_df = pd.merge(init_df, df, left_index=True, right_index=True, how='outer')
            init_df = init_df.sum(axis=1)
            init_df = pd.DataFrame(init_df)

            if team_or_driver=='driver' or team_or_driver==None:
                init_df.columns = ['constructor_Id']
            else:
                init_df.columns = ['driver_Id']

        #print init_df.head()
        #print "==============="

    if init_df.empty:
        return None, None

    if team_or_driver=='driver' or team_or_driver==None:
        init_df.sort_values('constructor_Id', ascending=False, inplace=True)
        print (init_df.head())
        init_df = init_df[init_df.constructor_Id==int(init_df.max())]
    else:
        init_df.sort_values('driver_Id', ascending=False, inplace=True)
        print (init_df.head())
        init_df = init_df[init_df.driver_Id==int(init_df.max())]

    print (init_df.head())

    return [tuple(x) for x in init_df.to_records()]

def drivers_of_team(gp_name, circuit_name, locality, country, year, constructor_name):
    year, race_round, gp_names = get_race_round_and_gp_names(year, gp_name, circuit_name, locality, country)

    returned_drivers = []
    raw_drivers = []

    if race_round!=[0]:
        for race in race_round:
            results = drivers_of_team_in_race(year, race, constructor_name)

            if isinstance(results, str) and results=='data_NA':
                return 'data_NA', None, None

            returned_drivers.append([driver_mapping[i] for i in results.driver_Id])
            raw_drivers.append([i for i in results.driver_Id])

    return returned_drivers, raw_drivers, gp_names

def team_of_driver(gp_name, circuit_name, locality, country, year, driver_name):
    year, race_round, gp_names = get_race_round_and_gp_names(year, gp_name, circuit_name, locality, country)

    returned_constructors = []
    raw_constructors = []

    if race_round!=[0]:
        for race in race_round:
            results = team_of_driver_in_race(year, race, driver_name)

            if isinstance(results, str) and results=='data_NA':
                return 'data_NA', None, None

            returned_constructors.append([constuctor_mapping[i] for i in results.constructor_Id])
            raw_constructors.append([i for i in results.constructor_Id])

    return returned_constructors, raw_constructors, gp_names

def next_race(gp_name, circuit_name, locality, country):
    year = '2017'
    race_schedule = yearly_race_schedule(year)
    race_round, gp_name, race_date, race_time = next_specific_race(gp_name, circuit_name, locality, country, race_schedule)

    if race_round!=None:
        return gp_name, race_date, race_time
    else:
        return None, None, None


def standings(year=None, top_bottom=None, numeric=None, ordinal=None, \
            driver_name=None, constructor_name=None, team_or_driver=None):

    if driver_name!=None:
        team_or_driver = 'driver'
    elif constructor_name!=None:
        team_or_driver = 'team'

    results, year = year_standings(year, team_or_driver)

    if isinstance(results, str) and results=='data_NA':
        return 'data_NA', None, None, None, None, None, None

    #Get specific driver or constructor
    if driver_name!=None or constructor_name!=None:
        if constructor_name!=None:
            this_positions = list(results[results.constructor_Id==constructor_name]['constructor_position'].values)
            this_points = list(results[results.constructor_Id==constructor_name]['points'].values)
            this_drivers = []
            this_constructors = [constructor_name]
        else:
            this_positions = list(results[results.driver_Id==driver_name]['driver_position'].values)
            this_points = list(results[results.driver_Id==driver_name]['points'].values)
            this_drivers = [driver_name]
            this_constructors = []
            #TODO: change text to 'Retired' for example

    #Get specific number
    elif isinstance(ordinal, int): #and top_bottom==None
        if results.shape[0]<ordinal:
            return results.shape[0], None, None, None, None, None, None
        if team_or_driver=='team':
            this_constructors = [results.iloc[ordinal-1]['constructor_Id']]
            this_drivers = []
            this_points = [results.iloc[ordinal-1]['points']]
            this_positions = []
        else:
            this_constructors = []
            this_drivers = [results.iloc[ordinal-1]['driver_Id']]
            this_points = [results.iloc[ordinal-1]['points']]
            this_positions = []

    #Get top N drivers
    elif (top_bottom=='top' or ordinal==1): #and isinstance(numeric, int)
        #This is for the question "who was the winner in that race?"
        if numeric==None:
            numeric = 1

        if results.shape[0]<numeric:
            return results.shape[0], None, None, None, None, None, None

        if team_or_driver=='team':
            this_constructors = list(results.head(numeric)['constructor_Id'])
            this_drivers = []
            this_points = list(results.head(numeric)['points'])
            this_positions = []
        else:
            this_constructors = []
            this_drivers = list(results.head(numeric)['driver_Id'])
            this_points = list(results.head(numeric)['points'])
            this_positions = []

    #Get bottom N teams
    elif top_bottom=='bottom': #and isinstance(numeric, int)
        #This is for the question "which is the last team in the standings?"
        if numeric==None:
            numeric = 1

        if results.shape[0]<numeric:
            return results.shape[0], None, None, None, None, None, None

        if team_or_driver=='team':
            this_constructors = list(results.tail(numeric)['constructor_Id'])
            this_drivers = []
            this_points = list(results.tail(numeric)['points'])
            this_positions = []
        else:
            this_constructors = []
            this_drivers = list(results.tail(numeric)['driver_Id'])
            this_points = list(results.tail(numeric)['points'])
            this_positions = []

    else:
        if team_or_driver=='team':
            this_constructors = list(results['constructor_Id'])
            this_drivers = []
            this_points = list(results['points'])
            this_positions = []
        else:
            this_constructors = []
            this_drivers = list(results['driver_Id'])
            this_points = list(results['points'])
            this_positions = []

    returned_constructors = [constuctor_mapping[i] for i in this_constructors]
    returned_drivers = [driver_mapping[i] for i in this_drivers]
    returned_positions = this_positions
    returned_points = this_points
    raw_constructors = [i for i in this_constructors]
    raw_drivers = [i for i in this_drivers]

    return returned_constructors, returned_drivers, returned_positions, \
            raw_constructors, raw_drivers, returned_points, year

def fastest_laps(gp_name, circuit_name, locality, country, year):

    year, race_round, gp_names = get_race_round_and_gp_names(year, gp_name, circuit_name, locality, country)

    returned_drivers = []
    returned_constructors = []
    returned_times = []
    raw_constructors = []
    raw_drivers = []
    returned_lap_rounds = []

    if race_round!=[0]:
        for race in race_round:
            fastest_lap_time, driver_Id, constructor_Id, fastest_lap_time_round = \
                        fastest_lap(year, race)

            if (isinstance(fastest_lap_time, str) and fastest_lap_time=='data_NA') or \
                fastest_lap_time==None:
                return 'data_NA', None, None, None, None, None, None, None

            returned_constructors.append(constuctor_mapping[constructor_Id])
            returned_drivers.append(driver_mapping[driver_Id])
            returned_times.append(fastest_lap_time)
            raw_constructors.append(constructor_Id)
            raw_drivers.append(driver_Id)
            returned_lap_rounds.append(fastest_lap_time_round)

    return returned_constructors, returned_drivers, returned_times, gp_names, \
            raw_constructors, raw_drivers, year, returned_lap_rounds

def get_current_drivers():
    drivers_soup = url_to_soup('http://ergast.com/api/f1/current/drivers/')
    current_drivers = []
    for driver in drivers_soup.find('drivertable').find_all('driver'):
        current_drivers.append(driver['driverid'])

    return current_drivers

def get_current_constructors():
    constructors_soup = url_to_soup('http://ergast.com/api/f1/current/constructors/')
    current_constructors = []
    for constructor in constructors_soup.find('ConstructorTable').find_all('Constructor'):
        current_constructors.append(constructor['constructorId'])

    return current_constructors


def social_media_accounts(driver, constructor):
    data = pd.read_csv('f1_twitter_accounts.csv')

    if driver!=None:
        if driver in data.driver_or_team.values:
            return data[data['driver_or_team']==driver]['tw_account'].values[0]
        elif driver in get_current_drivers():
            return 'no_account'
        else:
            return 'not_current'
    elif constructor!=None:
        if constructor in data.driver_or_team.values:
            return data[data['driver_or_team']==constructor]['tw_account'].values[0]
        elif constructor in get_current_constructors():
            return 'no_account'
        else:
            return 'not_current'

#teammates(None, None, None, None, None, 'button')
#teammates(None, None, None, None, 2012, 'alonso')
#teammates(None, None, None, 'italy', 2012, 'alonso')
#teammates(None, None, None, 'spain', 2008, 'alonso')
def teammates(gp_name, circuit_name, locality, country, year, driver):
    year, race_round, gp_names = get_race_round_and_gp_names(year, gp_name, circuit_name, locality, country)

    returned_driver = None
    raw_driver = None

    if race_round!=[0]:
        for race in race_round:
            results = team_of_driver_in_race(year, race, driver)

            if isinstance(results, str) and results=='data_NA':
                return 'data_NA', None, None

            results = drivers_of_team_in_race(year, race, results['constructor_Id'].values[0])

            if isinstance(results, str) and results=='data_NA':
                return 'data_NA', None, None

            raw_driver = results[results.driver_Id!=driver].values[0][0]
            returned_driver = driver_mapping[raw_driver]

    return returned_driver, raw_driver, gp_names[len(gp_names)-1]

def driver_or_team_info(driver, constructor):
    if driver!=None:
        url = "http://ergast.com/api/f1/drivers/" + driver
        soup = url_to_soup(url)
        url = soup.find('driver')['url']
        birthday = soup.find('driver').find('dateofbirth').text
        birthday = datetime.strptime(birthday, '%Y-%m-%d').strftime('%d-%m-%Y')
        nationality = soup.find('driver').find('nationality').text
    else:
        url = "http://ergast.com/api/f1/constructors/" + constructor
        soup = url_to_soup(url)
        url = soup.find('constructor')['url']
        birthday = None
        nationality = soup.find('constructor').find('nationality').text

    return url, nationality, birthday

def driver_homeland(driver):
    if driver!=None:
        url = "http://ergast.com/api/f1/drivers/" + driver
        soup = url_to_soup(url)
        url = soup.find('driver')['url']
        birthday = soup.find('driver').find('dateofbirth').text
        birthday = datetime.strptime(birthday, '%Y-%m-%d').strftime('%d-%m-%Y')
        nationality = soup.find('driver').find('nationality').text
        hometown = wiki_hometown(url)
    return url, nationality, birthday

def wiki_hometown(url):
    #url = "http://ergast.com/api/f1/drivers/" + driver
    url = url.replace("http", "https")
    soup = url_to_soup(url)
    biography = soup.find('table',{'class':'vcard'})
    details = biography.find_all('a')
    hometown = details[-1]

    return hometown

def get_season_review_url(year):
    url = "http://ergast.com/api/f1/seasons?limit=200&offset=0"
    soup = url_to_soup(url)

    for season in soup.find_all('Season'):
        if int(year) == int(season.text):
            return season['url']