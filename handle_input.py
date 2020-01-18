from wit import Wit
import random
import sys
from langdetect import detect
import json

import string
import re

from ergast_API import race_result, quali_result, drivers_of_team, team_of_driver, \
                next_race, standings, aggregate_stats, fastest_laps, quali_times, \
                pit_stop_times, retirement_reason, retirees, social_media_accounts, \
                most_aggregate_stats, championship_results, most_championship_results, \
                compare_drivers_or_teams, aggregate_quali_stats,\
                most_aggregate_quali_stats, get_current_drivers, teammates, \
                driver_or_team_info, driver_homeland, appearances_stats, get_season_review_url
from utils import integer_to_ordinal, proper_language, clean_dict, \
            audio_to_text
import tgen
from play_game import run_game
from f1com_stuff import latest_news_to_generic, flags_to_generic, tickets_button_list
from mappings import constuctor_mapping, driver_mapping
from fb_buttons import create_image_or_video_fb_format

GREETINGS = ['Hi there', 'Hello']
HOW_AM_I = ['I\'m fine thank you! What about you?', 'A bit tired talking so much lately. And you?', \
            'I\'m great! Go ahead and ask me something.']
THANKS = ['Always happy to answer your questions!', 'You are welcome :slightly_smiling_face:']
WTF = ["I cannot understand what you say. Please rephrase or ask something related to F1!", \
        "I beg your pardon? Please rephrase or ask something related to F1!",
        "Can you please rephrase? I cannnot understand you."]
DATA_NA = ["I'm sorry but I cannot find the data to your question. Try something else please."]

DRIVER_WORDS = ['he', 'his', 'him', 'the driver', 'this driver', 'that driver']
CONSTRUCTOR_WORDS = ['the team', 'that team', 'this team']
RACE_WORDS = ['this race', 'that race', 'this circuit', 'that circuit', 'there',\
                'this country', 'that country', 'this gp', 'that gp', 'same race']
YEAR_WORDS = RACE_WORDS + ['this year', 'that year', 'this season', 'that season']

def read_context(user_id = 'stergios'):
    context_filename = "contexts.txt"
    contexts = json.load(open(context_filename))

    context = {}
    for this_context in contexts:
        if this_context['user_id']== user_id:
            context = this_context
            context = context['payload']
            break
    return context


def write_context(user_id, payload):
    context_filename = "contexts.txt"
    user_existed = False
    contexts = []
    contexts = json.load(open(context_filename))
    for this_context in contexts:
        if this_context['user_id'] == user_id:
            user_existed = True
            this_context.update((k, payload) for k, v in this_context.iteritems() if k == "payload")

    ##if user_existed==False:
     ##   contexts.append({'user_id': user_id, 'payload': payload})

    json.dump(contexts, open(context_filename,'w'))

def create_bigrams(text):
    regex = re.compile('[%s]' % re.escape(string.punctuation))
    text = regex.sub('', text)
    splitted_text = text.split()
    splitted_text.extend([a + ' ' + b for a, b in zip(splitted_text[:-1], splitted_text[1:])])
    return splitted_text

def get_key_at_index(CONTEXT, key, index):
    if key in CONTEXT.keys() and isinstance(CONTEXT[key], list) and len(CONTEXT[key])>0:
        return CONTEXT[key][index]
    elif key in CONTEXT.keys():
        return CONTEXT[key]
    else:
        return None

def get_key_as_list(CONTEXT, key):
    if key in CONTEXT.keys() and isinstance(CONTEXT[key], list) and len(CONTEXT[key])>0:
        return CONTEXT[key]
    elif key in CONTEXT.keys():
        return [CONTEXT[key]]
    else:
        return None

def get_variable(request, CONTEXT, key, index=0, intent = '', get_all=False, request_only=False):
    try:
        if request_only==False:
            if get_all:
                if key in request['entities'].keys():
                    return [m['value'] for m in request['entities'][key]]

                else:
                    if intent!='':
                        if key == 'driver' and any([i for i in DRIVER_WORDS if i in create_bigrams(request['_text'])]):
                            return get_key_as_list(CONTEXT, key)
                        elif key == 'constructor' and any([i for i in CONSTRUCTOR_WORDS if i in create_bigrams(request['_text'])]):
                            return get_key_as_list(CONTEXT, key)
                        elif key in ['gp_name', 'circuit_name', 'locality', 'country'] and \
                                any([i for i in RACE_WORDS if i in create_bigrams(request['_text'])]):
                            return get_key_as_list(CONTEXT, key)
                        elif key == 'year' and any([i for i in YEAR_WORDS if i in create_bigrams(request['_text'])]):
                            return get_key_as_list(CONTEXT, key)
                        else:
                            return None
                    else:
                        return get_key_as_list(CONTEXT, key)

            if key in request['entities'].keys():
                return request['entities'][key][index]['value']
            else:
                if intent!='':
                    if key == 'driver' and any([i for i in DRIVER_WORDS if i in create_bigrams(request['_text'])]):
                        return get_key_at_index(CONTEXT, key, index)
                    elif key == 'constructor' and any([i for i in CONSTRUCTOR_WORDS if i in create_bigrams(request['_text'])]):
                        return get_key_at_index(CONTEXT, key, index)
                    elif key in ['gp_name', 'circuit_name', 'locality', 'country'] and \
                            any([i for i in RACE_WORDS if i in create_bigrams(request['_text'])]):
                        return get_key_at_index(CONTEXT, key, index)
                    elif key == 'year' and any([i for i in YEAR_WORDS if i in create_bigrams(request['_text'])]):
                        return get_key_at_index(CONTEXT, key, index)
                    else:
                        return None
                else:
                    return get_key_at_index(CONTEXT, key, index)
        else:
            if get_all:
                if key in request['entities'].keys():
                    return [m['value'] for m in request['entities'][key]]

            if key in request['entities'].keys():
                return request['entities'][key][index]['value']

    except Exception:
        return None

    return None


#unused_entities = [u'spanoulis', u'bottom', u'PALAU BLAUGRANA', 'against', 1]
def handle_confusing_question(request, useful_entities):
    harmless_entities = set(['against', 'slack', 'microphone', 'yes', 'no', 'top', 'bottom'])
    useful_harmless_entities = ['yes', 'no', 'top', 'bottom', 'most', 'least']

    common_entities = [i for i in request['entities'].keys() if i in useful_entities]

    unused_entities = [get_variable(request, {}, i, 0,  '', get_all=True) for i in \
                        request['entities'].keys() if i not in useful_entities]
    unused_entities = [item for sublist in unused_entities for item in sublist]

    harmless_entities = [i for i in unused_entities if i in list(harmless_entities)]
    useful_harmless_entities = [i for i in useful_harmless_entities if i in \
                            list(harmless_entities) and i in useful_entities]
    if 'year' in useful_entities or 'number' in useful_entities:
        useful_harmless_entities.extend([x for x in unused_entities if isinstance(x, int)])

    unused_entities = list(set(unused_entities) - set(harmless_entities))
    unused_entities = [x for x in unused_entities if not isinstance(x, int)]


    if 'intent' not in request['entities'].keys() and \
        len(request['entities'].keys())>0 and \
        (len(common_entities)==0 or len(unused_entities)>=1) and \
        len(useful_harmless_entities)==0:

#        players = []
#        teams = []
#        metrics = []
#        stadiums = []
#        for i, entity in enumerate(unused_entities):
#            if entity.lower() in player_map.keys():
#                unused_entities[i] = " ".join([j.strip() for j in correct_player_name(entity).title().split(',')])
#                players.append(unused_entities[i])
#            elif entity.lower() in team_map.keys():
#                unused_entities[i] = correct_team_name(entity)
#                teams.append(unused_entities[i])
#            elif entity.lower() in metric_map.keys():
#                metrics.append(entity.lower())
#            elif entity.lower() in stadiums_list:
#                unused_entities[i] = entity.title()
#                stadiums.append(entity.title())
#
#        unused_entities = players + teams + metrics + stadiums
#        print "Used entities: " + connect_text_list(unused_entities)

        #TODO: Insert unused_entities into the CONTEXT

        if unused_entities==[]:
            response = random.choice(WTF)
        elif len(unused_entities)==1:
            response = unused_entities[0] + " what? I didn't get that, I'm sorry!"
            response = response[0].capitalize() + response[1:]
        else:
             response = "I'm afraid I didn't understand. What about " + \
                        tgen.text_for_many_items(unused_entities) + "?"
    else:
        response = None

    return response

def clear_context_and_call_function(useful_entities, function, request, \
                intent, previous_intent, CONTEXT, is_quali='', user_id=''):

    CONTEXT = keep_only_needed_variables_in_context(CONTEXT, useful_entities)
    confusing_question = handle_confusing_question(request, useful_entities)
    if confusing_question!=None:
        resp, CONTEXT = confusing_question, CONTEXT
    else:
        if is_quali!='':
            print ("A")
            resp, CONTEXT = function(request, intent, previous_intent, CONTEXT, \
                                    is_quali)
        else:
            print ("B")
            resp, CONTEXT = function(request, intent, previous_intent, CONTEXT=CONTEXT)

    return resp, CONTEXT

def keep_only_needed_variables_in_context(CONTEXT, useful_entities):
    for key in CONTEXT.keys():
        if key not in useful_entities and key!='intent':
            CONTEXT.pop(key, None)
    return CONTEXT

def key_exists_and_equals(response, key, value):
    if key in response['entities'].keys() and response['entities'][key][0]['value']==value:
        return True
    else:
        return False

def key_value(response, key):
    if key in response['entities'].keys():
        return response['entities'][key][0]['value']
    else:
        return ''


def handle_command(input_text, audio_url, user_id):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    CONTEXT = read_context(user_id)
    print ("CONTEXT= " + str(CONTEXT))
    sys.stdout.flush()

    init_response = ''

    if audio_url!='' and input_text=='':
        try:
            input_text = audio_to_text(audio_url)
            init_response = 'You said: ' + input_text + '.\n\n'
        except KeyboardInterrupt:
            input_text = ''
            init_response = 'long_audio'

    print ("DEBUG: ", input_text, init_response, audio_url)
    sys.stdout.flush()


    ##return "You said: ", str(input_text)
    #Connect to wit.ai
    f=open("appsettings/tokens.txt","r")
    lines=f.readlines()
    ACCESS_TOKEN=lines[2]
    f.close()

    client = Wit(access_token=ACCESS_TOKEN)

    if input_text!='':
        print ("You said: ", str(input_text))
        sys.stdout.flush()

        try:
            lang = detect(input_text)
        except Exception:
            lang = 'en'
        print ("Lang: ", str(lang))
        sys.stdout.flush()
        response = client.message(input_text)
        print ("request = response = " + str(response))

        if lang!='en' and len(input_text.split())>3 and response['entities']=={}:
            init_response = ''
            resp = proper_language(lang)
            print ("Lang text: ", str(resp))
            sys.stdout.flush()

        else:
            if response['entities']=={}:# and CONTEXT=={}:
                resp = random.choice(WTF)
            else:
                if 'intent' in response['entities'].keys():
                    intent = response['entities']['intent'][0]['value']
                else:
                    intent = ''
                    resp = random.choice(WTF)

                if 'intent' in CONTEXT.keys():
                    previous_intent = CONTEXT['intent']
                else:
                    previous_intent = ''

                if intent!='': #and (intent!=previous_intent)
                    previous_intent = ''
                    for key in response['entities'].keys():
                        CONTEXT.pop(key, None)

                if intent == 'race_result' or (intent == '' and previous_intent == 'race_result'):
                    useful_entities = ['year', 'number', 'podium', 'top_bottom', 'gp_name', \
                                       'circuit_name', 'locality', 'country', 'ordinal', \
                                       'driver', 'constructor', 'team_or_driver']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_race_or_quali_results, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT, is_quali=False)
                elif intent == 'qualifying_result' or (intent == '' and previous_intent == 'qualifying_result'):
                    useful_entities = ['year', 'number', 'podium', 'top_bottom', 'gp_name', \
                                       'circuit_name', 'locality', 'country', 'ordinal', \
                                       'driver', 'constructor', 'team_or_driver']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_race_or_quali_results, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT, is_quali=True)
                elif intent == 'quali_time' or (intent == '' and previous_intent == 'quali_time'):
                    useful_entities = ['year', 'number', 'top_bottom', 'gp_name', \
                                       'circuit_name', 'locality', 'country', 'ordinal', \
                                       'driver', 'constructor', 'team_or_driver', 'quali_period']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_quali_time, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'fastest_lap' or (intent == '' and previous_intent == 'fastest_lap'):
                    useful_entities = ['year', 'number', 'top_bottom', 'gp_name', \
                                       'circuit_name', 'locality', 'country']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_fastest_lap, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'pit_stops' or (intent == '' and previous_intent == 'pit_stops'):
                    useful_entities = ['year', 'number', 'gp_name', \
                                       'circuit_name', 'locality', 'country', \
                                       'driver', 'constructor', 'team_or_driver', 'top_bottom']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_pit_stops, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'aggregate_stats' or (intent == '' and previous_intent == 'aggregate_stats'):
                    useful_entities = ['year', 'number', 'podium', 'top_bottom', 'gp_name', \
                                       'circuit_name', 'locality', 'country', 'ordinal', \
                                       'driver', 'constructor', 'team_or_driver']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_aggregate_stats, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'most_aggregate_stats' or (intent == '' and previous_intent == 'most_aggregate_stats'):
                    useful_entities = ['year', 'number', 'podium', 'top_bottom', 'gp_name', \
                                       'circuit_name', 'locality', 'country', 'ordinal', \
                                       'team_or_driver']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_most_aggregate_stats, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'aggregate_quali_stats' or (intent == '' and previous_intent == 'aggregate_quali_stats'):
                    useful_entities = ['year', 'number', 'podium', 'top_bottom', 'gp_name', \
                                       'circuit_name', 'locality', 'country', 'ordinal', \
                                       'driver', 'constructor', 'team_or_driver']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_aggregate_quali_stats, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'most_aggregate_quali_stats' or (intent == '' and previous_intent == 'most_aggregate_quali_stats'):
                    useful_entities = ['year', 'number', 'podium', 'top_bottom', 'gp_name', \
                                       'circuit_name', 'locality', 'country', 'ordinal', \
                                       'team_or_driver']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_most_aggregate_quali_stats, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'championship_stats' or (intent == '' and previous_intent == 'championship_stats'):
                    useful_entities = ['number', 'top_bottom', 'ordinal', \
                                       'driver', 'constructor']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_championship_stats, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'most_championship_stats' or (intent == '' and previous_intent == 'most_championship_stats'):
                    useful_entities = ['year', 'number', 'podium', 'top_bottom', 'gp_name', \
                                       'circuit_name', 'locality', 'country', 'ordinal', \
                                       'team_or_driver']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_most_championship_stats, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'appearance_stats' or (intent == '' and previous_intent == 'appearance_stats'):
                    useful_entities = ['year', 'number', 'gp_name', \
                                       'circuit_name', 'locality', 'country', \
                                       'driver', 'constructor', 'team_or_driver']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_appearance_stats, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'most_appearance_stats' or (intent == '' and previous_intent == 'most_appearance_stats'):
                    useful_entities = ['year', 'number', 'gp_name', \
                                       'circuit_name', 'locality', 'country', \
                                       'team_or_driver']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_most_appearance_stats, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'drivers_of_team' or (intent == '' and previous_intent == 'drivers_of_team'):
                    useful_entities = ['year', 'gp_name', 'circuit_name', 'locality', \
                                        'country', 'constructor', 'number']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_drivers_of_team, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'team_of_driver' or (intent == '' and previous_intent == 'team_of_driver'):
                    useful_entities = ['year', 'gp_name', 'circuit_name', 'locality', \
                                        'country', 'driver', 'number']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_team_of_driver, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'race_schedule' or (intent == '' and previous_intent == 'race_schedule'):
                    useful_entities = ['gp_name', 'circuit_name', 'locality', 'country']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_race_schedule, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'standings' or (intent == '' and previous_intent == 'standings'):
                    useful_entities = ['year', 'number', 'top_bottom', 'ordinal', \
                                       'driver', 'constructor', 'team_or_driver']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_standings, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'free_practice' or (intent == '' and previous_intent == 'free_practice'):
                    useful_entities = ['year', 'number', 'podium', 'top_bottom', 'gp_name', \
                                       'circuit_name', 'locality', 'country', 'ordinal', \
                                       'driver', 'constructor', 'team_or_driver']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_free_practice, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'retirement_reason' or (intent == '' and previous_intent == 'retirement_reason'):
                    useful_entities = ['year', 'number', 'gp_name', \
                                       'circuit_name', 'locality', 'country', \
                                       'driver', 'constructor']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_retirement_reason, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'retirees' or (intent == '' and previous_intent == 'retirees'):
                    useful_entities = ['year', 'number', 'gp_name', \
                                       'circuit_name', 'locality', 'country']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_retirees, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'social_media' or (intent == '' and previous_intent == 'social_media'):
                    useful_entities = ['driver', 'constructor']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_social_media, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'team_or_driver_comparison' or (intent == '' and previous_intent == 'team_or_driver_comparison'):
                    useful_entities = ['driver', 'constructor']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_team_or_driver_comparison, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'latest_news' or (intent == '' and previous_intent == 'latest_news'):
                    useful_entities = []
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_latest_news, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'latest_videos' or (intent == '' and previous_intent == 'latest_videos'):
                    useful_entities = []
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_latest_videos, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'ticket' or (intent == '' and previous_intent == 'ticket'):
                    useful_entities = ['gp_name', 'circuit_name', 'locality', 'country']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_ticket, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'best_driver_or_team' or (intent == '' and previous_intent == 'best_driver_or_team'):
                    useful_entities = ['team_or_driver']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_best_driver_or_team, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'teammate' or (intent == '' and previous_intent == 'teammate'):
                    useful_entities = ['year', 'gp_name', 'circuit_name', 'locality', \
                                        'country', 'driver']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_teammate, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'flags' or (intent == '' and previous_intent == 'flags'):
                    useful_entities = ['flag_colours_shapes']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_flags, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'driver_or_team_info' or (intent == '' and previous_intent == 'driver_or_team_info'):
                    useful_entities = ['driver', 'constructor']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_driver_or_team_info, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'season_review' or (intent == '' and previous_intent == 'season_review'):
                    useful_entities = ['year', 'number']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_season_review, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'driver_homeland' or (intent == '' and previous_intent == 'driver_homeland'):
                    useful_entities = ['driver']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_driver_homeland, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'my_god' or (intent == '' and previous_intent == 'my_god'):
                    useful_entities = []
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_god, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'help' or (intent == '' and previous_intent == 'help'):
                    useful_entities = []
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_help, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)
                elif intent == 'play_game' or (intent == '' and previous_intent == 'play_game'):
                    useful_entities = ['year', 'number', 'podium', 'top_bottom', 'gp_name', \
                                       'circuit_name', 'locality', 'country', 'ordinal', \
                                       'driver', 'constructor', 'team_or_driver', \
                                       'correct_answers', 'num_questions', 'last_asked_question', \
                                       'questions_asked']
                    resp, CONTEXT = clear_context_and_call_function(useful_entities, get_play_game, \
                        request=response, intent=intent, previous_intent = previous_intent, CONTEXT=CONTEXT)

        if resp==None:
            resp = random.choice(WTF)

    elif init_response=='long_audio':
        init_response = ''
        resp = 'I could not understand what you said. Can you please ask me again?'

    if audio_url!='' and (input_text=='' or resp in WTF):
        init_response = ''
        resp = 'What you said was either unclear or unrelated to F1. Can you please ask me again?'

    print ("CONTEXT= " + str(CONTEXT))
    sys.stdout.flush()
    write_context(user_id, CONTEXT)

    if isinstance(resp, str) or isinstance(resp, str):
        resp = init_response + resp
        resp = [resp]
    elif isinstance(resp, dict):
        resp = [resp]
        resp.insert(0, init_response)
    elif isinstance(resp, list):
        if init_response!='':
            resp.insert(0, init_response)

    return resp


#WIT.AI code
def send(request, response):
    print(response['text'])

def get_god(request, intent, previous_intent, CONTEXT):
    CONTEXT = {}
    CONTEXT['intent'] = 'my_god'
    CONTEXT['driver'] = 'alonso'

    text = tgen.text_for_god()

    return text, CONTEXT


def get_race_or_quali_results(request, intent, previous_intent, CONTEXT, is_quali):

    if is_quali:
        CONTEXT['intent'] = 'qualifying_result'
    else:
        CONTEXT['intent'] = 'race_result'

#        gp_datetime = key_value(request, 'datetime')
#        if gp_datetime!='':
#            gp_datetime = datetime.strptime(gp_datetime[:10], '%Y-%m-%d')
#            year = gp_datetime.year
#            day = gp_datetime.day
#            month = gp_datetime.month
#
#            #If it is 1-Jan, then we only need to keep the year
#            if day==1 and month==1:
#                day = ''
#                month = ''
#
#        number = key_value(request, 'number')

    year = None
    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    year = get_variable(request, CONTEXT, 'year', 0, intent)
    if numbers!=None:
        for i in numbers:
            if i>=1000:
                year = i
            else:
                number = i

    podium = get_variable(request, CONTEXT, 'podium', 0, intent)
    top_bottom = get_variable(request, CONTEXT, 'top_bottom', 0, intent)
    if podium=='podium':
        top_bottom = 'top'
        number = 3

    pole = get_variable(request, CONTEXT, 'pole', 0, intent)
    if pole=='pole':
        top_bottom = 'top'
        number = 1

    if any([i in ['gp_name', 'circuit_name', 'locality', 'country'] for i in request['entities'].keys()]):
        CONTEXT.pop('gp_name', None)
        CONTEXT.pop('circuit_name', None)
        CONTEXT.pop('locality', None)
        CONTEXT.pop('country', None)

    gp_name = get_variable(request, CONTEXT, 'gp_name', 0, intent)
    circuit_name = get_variable(request, CONTEXT, 'circuit_name', 0, intent)
    locality = get_variable(request, CONTEXT, 'locality', 0, intent)
    country = get_variable(request, CONTEXT, 'country', 0, intent)
    ordinal = get_variable(request, CONTEXT, 'ordinal', 0, intent)
    driver = get_variable(request, CONTEXT, 'driver', 0, intent)
    constructor = get_variable(request, CONTEXT, 'constructor', 0, intent)
    team_or_driver = get_variable(request, CONTEXT, 'team_or_driver', 0, intent)

    if 'ordinal' in request['entities'].keys():
        number = None
        top_bottom = None
        CONTEXT.pop('number', None)
        CONTEXT.pop('top_bottom', None)
    elif ('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']<1000) or \
            'podium' in request['entities'].keys() or \
            'top_bottom' in request['entities'].keys():
        ordinal = None
        CONTEXT.pop('ordinal', None)

    if 'top_bottom' in request['entities'].keys() and \
            (('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']>=1000) or \
            ('number' not in request['entities'].keys())):
        number = None
        CONTEXT.pop('number', None)

    if 'constructor' in request['entities'].keys() or \
            ('team_or_driver' in request['entities'].keys() and \
            request['entities']['team_or_driver'][0]['value']=='team'):
        team_or_driver = 'team'
        driver = None
        CONTEXT.pop('driver', None)

    if 'driver' in request['entities'].keys() or \
            ('team_or_driver' in request['entities'].keys() and \
            request['entities']['team_or_driver'][0]['value']=='driver'):
        team_or_driver = 'driver'
        constructor = None
        CONTEXT.pop('constructor', None)

    if 'driver' in request['entities'].keys() or 'constructor' in request['entities'].keys():
        ordinal = None
        CONTEXT.pop('ordinal', None)

    #E.g. Who qualified 2nd in monza? And who won the race?
    if 'top_bottom' in request['entities'].keys() \
            or ('number' in request['entities'].keys() and request['entities']['number'][0]['value']<1000)\
            or 'podium' in request['entities'].keys() \
            or 'ordinal' in request['entities'].keys():
        driver = None
        constructor = None
        CONTEXT.pop('driver', None)
        CONTEXT.pop('constructor', None)

    y = {'intent':CONTEXT['intent'],
         'year': year,
           'number': [number],
           #'podium': podium,
           'top_bottom': top_bottom,
           'gp_name': gp_name,
           'circuit_name': circuit_name,
           'locality': locality,
           'country': country,
           'ordinal': ordinal,
           'driver': driver,
           'constructor': constructor,
           'team_or_driver': team_or_driver}
    CONTEXT = clean_dict(y)

    if is_quali:
        returned_constructors, returned_drivers, returned_positions, gp_names,\
        raw_constructors, raw_drivers, year= \
            quali_result(gp_name, circuit_name, locality, \
            country, year, top_bottom, number, ordinal, \
            driver, constructor, team_or_driver)
    else:
        returned_constructors, returned_drivers, returned_positions, gp_names,\
        raw_constructors, raw_drivers, year= \
            race_result(gp_name, circuit_name, locality, \
            country, year, top_bottom, number, ordinal, \
            driver, constructor, team_or_driver)

    if isinstance(returned_constructors, str) and returned_constructors=='data_NA':
        return random.choice(DATA_NA), CONTEXT

    #If only fewer drivers took part
    if isinstance(returned_constructors, int):
        text = "There were only " + str(returned_constructors) + " drivers in that session."
        return text, CONTEXT

    if len(raw_constructors[0])==1 and raw_constructors[0]:
        CONTEXT['constructor'] = raw_constructors[0][0]
    if len(raw_drivers[0])==1 and raw_drivers[0]:
        CONTEXT['driver'] = raw_drivers[0][0]

    #Non empty values
    lst = [gp_name, circuit_name, locality, country, year]
    lst = [i for i in lst if i!=None]

    lst_no_gp = [circuit_name, locality, country, year]
    lst_no_gp = [i for i in lst_no_gp if i!=None]

    if len(gp_names)==0:
        text = "There was no " + tgen.no_such_race_text(lst_no_gp, gp_name) + "."
    else:
        text = []
        if len(gp_names)>1:
            if gp_name!=None:
                text.append("There were " + str(len(gp_names)) + gp_names + "s in " + \
                        ' in '.join([str(i).title() for i in lst]) + ".")
            else:
                text.append("There were " + str(len(gp_names)) + " races in " + \
                        ' in '.join([str(i).title() for i in lst_no_gp]) + ".")

        if (team_or_driver=='team' or constructor!=None):
            for race_no in range(len(returned_constructors)):
                text.extend(tgen.text_for_race_result(returned_constructors[race_no], \
                        returned_positions[race_no], gp_names[race_no], top_bottom, number, \
                        ordinal, driver, constructor, team_or_driver, is_quali, year))
        else:
            for race_no in range(len(returned_drivers)):
                text.extend(tgen.text_for_race_result(returned_drivers[race_no], \
                        returned_positions[race_no], gp_names[race_no], top_bottom, number, \
                        ordinal, driver, constructor, team_or_driver, is_quali, year))

    return text, CONTEXT

def get_quali_time(request, intent, previous_intent, CONTEXT):

    CONTEXT['intent'] = 'quali_time'

    year = None
    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    year = get_variable(request, CONTEXT, 'year', 0, intent)
    if numbers!=None:
        for i in numbers:
            if i>=1000:
                year = i
            else:
                number = i

    top_bottom = get_variable(request, CONTEXT, 'top_bottom', 0)

    if any([i in ['gp_name', 'circuit_name', 'locality', 'country'] for i in request['entities'].keys()]):
        CONTEXT.pop('gp_name', None)
        CONTEXT.pop('circuit_name', None)
        CONTEXT.pop('locality', None)
        CONTEXT.pop('country', None)
        CONTEXT.pop('quali_period', None)

    gp_name = get_variable(request, CONTEXT, 'gp_name', 0, intent)
    circuit_name = get_variable(request, CONTEXT, 'circuit_name', 0, intent)
    locality = get_variable(request, CONTEXT, 'locality', 0, intent)
    country = get_variable(request, CONTEXT, 'country', 0, intent)
    ordinal = get_variable(request, CONTEXT, 'ordinal', 0, intent)
    driver = get_variable(request, CONTEXT, 'driver', 0, intent)
    constructor = get_variable(request, CONTEXT, 'constructor', 0, intent)
    team_or_driver = get_variable(request, CONTEXT, 'team_or_driver', 0, intent)
    quali_period = get_variable(request, CONTEXT, 'quali_period', 0, intent)

    if 'ordinal' in request['entities'].keys():
        number = None
        top_bottom = None
        CONTEXT.pop('number', None)
        CONTEXT.pop('top_bottom', None)
    elif ('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']<1000) or \
            'top_bottom' in request['entities'].keys():
        ordinal = None
        CONTEXT.pop('ordinal', None)

    if 'top_bottom' in request['entities'].keys() and \
            (('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']>=1000) or \
            ('number' not in request['entities'].keys())):
        number = None
        CONTEXT.pop('number', None)

    if 'constructor' in request['entities'].keys() or \
            ('team_or_driver' in request['entities'].keys() and \
            request['entities']['team_or_driver'][0]['value']=='team'):
        team_or_driver = 'team'
        driver = None
        CONTEXT.pop('driver', None)

    if 'driver' in request['entities'].keys() or \
            ('team_or_driver' in request['entities'].keys() and \
            request['entities']['team_or_driver'][0]['value']=='driver'):
        team_or_driver = 'driver'
        constructor = None
        CONTEXT.pop('constructor', None)

    if 'driver' in request['entities'].keys() or 'constructor' in request['entities'].keys():
        ordinal = None
        CONTEXT.pop('ordinal', None)

    #E.g. Who qualified 2nd in monza? And who won the race?
    if 'top_bottom' in request['entities'].keys() \
            or ('number' in request['entities'].keys() and request['entities']['number'][0]['value']<1000)\
            or 'ordinal' in request['entities'].keys():
        driver = None
        constructor = None
        CONTEXT.pop('driver', None)
        CONTEXT.pop('constructor', None)

    y = {'intent':CONTEXT['intent'],
         'year': year,
           'number': [number],
           'top_bottom': top_bottom,
           'gp_name': gp_name,
           'circuit_name': circuit_name,
           'locality': locality,
           'country': country,
           'ordinal': ordinal,
           'driver': driver,
           'constructor': constructor,
           'team_or_driver': team_or_driver,
           'quali_period' : quali_period}
    CONTEXT = clean_dict(y)
#    z = CONTEXT.copy()
#    z.update(y)
#    CONTEXT = z

    returned_constructors, returned_drivers, returned_times, gp_names,\
    raw_constructors, raw_drivers, year, returned_quali_phases = \
            quali_times(gp_name, circuit_name, locality, \
            country, year, top_bottom, number, ordinal, \
            driver, constructor, team_or_driver, quali_period)

    print (returned_constructors, returned_drivers, returned_times, gp_names,\
    raw_constructors, raw_drivers, year, returned_quali_phases)

    if isinstance(returned_constructors, str) and returned_constructors=='data_NA':
        return random.choice(DATA_NA), CONTEXT
    elif isinstance(returned_constructors, str) and returned_constructors=='q_NA':
        text = "There was no " + quali_period + " in that race."
        return text, CONTEXT

    #If only fewer drivers took part
    if isinstance(returned_constructors, int):
        text = "There were only " + str(returned_constructors) + " drivers in that session."
        return text, CONTEXT

    if len(raw_constructors[0])==1 and raw_constructors[0]:
        CONTEXT['constructor'] = raw_constructors[0][0]
    if len(raw_drivers[0])==1 and raw_drivers[0]:
        CONTEXT['driver'] = raw_drivers[0][0]

    #Non empty values
    lst = [gp_name, circuit_name, locality, country, year]
    lst = [i for i in lst if i!=None]

    lst_no_gp = [circuit_name, locality, country, year]
    lst_no_gp = [i for i in lst_no_gp if i!=None]

    if len(gp_names)==0:
        text_1 = ["There was no " + tgen.no_such_race_text(lst_no_gp, gp_name) + "."]
    else:
        text_1 = []
        if len(gp_names)>1:
            if gp_name!=None:
                text_1.append("There were " + str(len(gp_names)) + gp_names + "s in " + \
                        ' in '.join([str(i).title() for i in lst]) + ".")
            else:
                text_1.append("There were " + str(len(gp_names)) + " races in " + \
                        ' in '.join([str(i).title() for i in lst_no_gp]) + ".")

        for race_no in range(len(returned_constructors)):
            text_2 = tgen.text_for_quali_time(returned_constructors[race_no], \
                    returned_drivers[race_no], \
                    returned_times[race_no], gp_names[race_no], top_bottom, number, \
                    ordinal, driver, constructor, team_or_driver, year, \
                    returned_quali_phases[race_no])
            text_1 = text_1 + text_2

    return text_1, CONTEXT

def get_fastest_lap(request, intent, previous_intent, CONTEXT):

    CONTEXT['intent'] = 'fastest_lap'

    year = None
    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    year = get_variable(request, CONTEXT, 'year', 0, intent)
    if numbers!=None:
        for i in numbers:
            if i>=1000:
                year = i
            else:
                number = i

    if any([i in ['gp_name', 'circuit_name', 'locality', 'country'] for i in request['entities'].keys()]):
        CONTEXT.pop('gp_name', None)
        CONTEXT.pop('circuit_name', None)
        CONTEXT.pop('locality', None)
        CONTEXT.pop('country', None)

    gp_name = get_variable(request, CONTEXT, 'gp_name', 0, intent)
    circuit_name = get_variable(request, CONTEXT, 'circuit_name', 0, intent)
    locality = get_variable(request, CONTEXT, 'locality', 0, intent)
    country = get_variable(request, CONTEXT, 'country', 0, intent)

    y = {'intent':CONTEXT['intent'],
         'year': year,
           'number': [number],
           'gp_name': gp_name,
           'circuit_name': circuit_name,
           'locality': locality,
           'country': country}
    CONTEXT = clean_dict(y)
#    z = CONTEXT.copy()
#    z.update(y)
#    CONTEXT = z

    returned_constructors, returned_drivers, returned_times, gp_names, \
            raw_constructors, raw_drivers, year, returned_lap_rounds = \
            fastest_laps(gp_name, circuit_name, locality, country, year)

    if isinstance(returned_constructors, str) and returned_constructors=='data_NA':
        return random.choice(DATA_NA), CONTEXT

    if len(raw_constructors)==1 and raw_constructors[0]:
        CONTEXT['constructor'] = raw_constructors[0]
    if len(raw_drivers)==1 and raw_drivers[0]:
        CONTEXT['driver'] = raw_drivers[0]

    #Non empty values
    lst = [gp_name, circuit_name, locality, country, year]
    lst = [i for i in lst if i!=None]

    lst_no_gp = [circuit_name, locality, country, year]
    lst_no_gp = [i for i in lst_no_gp if i!=None]

    text_1 = []
    if len(gp_names)==0:
        text_1.append("There was no " + tgen.no_such_race_text(lst_no_gp, gp_name) + ".")
    else:
        if len(gp_names)>1:
            if gp_name!=None:
                text_1.append("There were " + str(len(gp_names)) + gp_names + "s in " + \
                        ' in '.join([str(i).title() for i in lst]) + ".")
            else:
                text_1.append("There were " + str(len(gp_names)) + " races in " + \
                        ' in '.join([str(i).title() for i in lst_no_gp]) + ".")

        for race_no in range(len(returned_constructors)):
            text_2 = tgen.text_for_fastest_lap(returned_constructors[race_no], \
                    returned_times[race_no], returned_drivers[race_no], \
                    gp_names[race_no], year, returned_lap_rounds[race_no])
            text_1 = text_1 + text_2

    return text_1, CONTEXT

def get_retirement_reason(request, intent, previous_intent, CONTEXT):

    CONTEXT['intent'] = 'retirement_reason'

    year = None
    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    year = get_variable(request, CONTEXT, 'year', 0, intent)
    if numbers!=None:
        for i in numbers:
            if i>=1000:
                year = i
            else:
                number = i

    if any([i in ['gp_name', 'circuit_name', 'locality', 'country'] for i in request['entities'].keys()]):
        CONTEXT.pop('gp_name', None)
        CONTEXT.pop('circuit_name', None)
        CONTEXT.pop('locality', None)
        CONTEXT.pop('country', None)

    gp_name = get_variable(request, CONTEXT, 'gp_name', 0, intent)
    circuit_name = get_variable(request, CONTEXT, 'circuit_name', 0, intent)
    locality = get_variable(request, CONTEXT, 'locality', 0, intent)
    country = get_variable(request, CONTEXT, 'country', 0, intent)
    driver = get_variable(request, CONTEXT, 'driver', 0, intent)
    constructor = get_variable(request, CONTEXT, 'constructor', 0, intent)

    if 'constructor' in request['entities'].keys():
        driver = None
        CONTEXT.pop('driver', None)

    if 'driver' in request['entities'].keys():
        constructor = None
        CONTEXT.pop('constructor', None)

    y = {'intent':CONTEXT['intent'],
         'year': year,
           'gp_name': gp_name,
           'circuit_name': circuit_name,
           'locality': locality,
           'country': country,
           'driver': driver,
           'constructor': constructor}
    CONTEXT = clean_dict(y)

    if driver==None and constructor==None:
        text = "Which driver or team are you talking about?"
        return text, CONTEXT

    returned_reasons, year, gp_names = \
            retirement_reason(gp_name, circuit_name, locality, \
            country, year, driver, constructor)

    print (returned_reasons)

    if isinstance(retirement_reason, str) and retirement_reason=='data_NA':
        return random.choice(DATA_NA), CONTEXT
    elif isinstance(retirement_reason, str) and retirement_reason=='no_retirement' and \
        driver==None and constructor==None:
        text = "Noone retired in that race."
        return text, CONTEXT

    #Non empty values
    lst = [gp_name, circuit_name, locality, country, year]
    lst = [i for i in lst if i!=None]

    lst_no_gp = [circuit_name, locality, country, year]
    lst_no_gp = [i for i in lst_no_gp if i!=None]

    if len(gp_names)==0:
        text_1 = ["There was no " + tgen.no_such_race_text(lst_no_gp, gp_name) + "."]
    else:
        text_1 = []
        if len(gp_names)>1:
            if gp_name!=None:
                text_1.append("There were " + str(len(gp_names)) + gp_names + "s in " + \
                        ' in '.join([str(i).title() for i in lst]) + ".")
            else:
                text_1.append("There were " + str(len(gp_names)) + " races in " + \
                        ' in '.join([str(i).title() for i in lst_no_gp]) + ".")

        for race_no in range(len(returned_reasons)):
            text_2 = tgen.text_for_retirement_reason(returned_reasons[race_no], \
                    gp_names[race_no], driver, constructor, year)
            text_1 = text_1 + text_2

    return text_1, CONTEXT

def get_retirees(request, intent, previous_intent, CONTEXT):

    CONTEXT['intent'] = 'retirees'

    year = None
    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    year = get_variable(request, CONTEXT, 'year', 0, intent)
    if numbers!=None:
        for i in numbers:
            if i>=1000:
                year = i
            else:
                number = i

    if any([i in ['gp_name', 'circuit_name', 'locality', 'country'] for i in request['entities'].keys()]):
        CONTEXT.pop('gp_name', None)
        CONTEXT.pop('circuit_name', None)
        CONTEXT.pop('locality', None)
        CONTEXT.pop('country', None)

    gp_name = get_variable(request, CONTEXT, 'gp_name', 0, intent)
    circuit_name = get_variable(request, CONTEXT, 'circuit_name', 0, intent)
    locality = get_variable(request, CONTEXT, 'locality', 0, intent)
    country = get_variable(request, CONTEXT, 'country', 0, intent)

    y = {'intent':CONTEXT['intent'],
         'year': year,
           'gp_name': gp_name,
           'circuit_name': circuit_name,
           'locality': locality,
           'country': country}
    CONTEXT = clean_dict(y)
#    z = CONTEXT.copy()
#    z.update(y)
#    CONTEXT = z

    returned_retirees, year, gp_names = \
            retirees(gp_name, circuit_name, locality, country, year)

    print (returned_retirees)

    if isinstance(retirement_reason, str) and retirement_reason=='data_NA':
        return random.choice(DATA_NA), CONTEXT
    elif isinstance(retirement_reason, str) and retirement_reason=='no_retirement':
        text = "Noone retired in that race."
        return text, CONTEXT

    #Non empty values
    lst = [gp_name, circuit_name, locality, country, year]
    lst = [i for i in lst if i!=None]

    lst_no_gp = [circuit_name, locality, country, year]
    lst_no_gp = [i for i in lst_no_gp if i!=None]

    if len(gp_names)==0:
        text_1 = ["There was no " + tgen.no_such_race_text(lst_no_gp, gp_name) + "."]
    else:
        text_1 = []
        if len(gp_names)>1:
            if gp_name!=None:
                text_1.append("There were " + str(len(gp_names)) + gp_names + "s in " + \
                        ' in '.join([str(i).title() for i in lst]) + ".")
            else:
                text_1.append("There were " + str(len(gp_names)) + " races in " + \
                        ' in '.join([str(i).title() for i in lst_no_gp]) + ".")

        for race_no in range(len(returned_retirees)):
            text_2 = tgen.text_for_retirees(returned_retirees[race_no], \
                    gp_names[race_no], year)
            text_1 = text_1 + text_2

    return text_1, CONTEXT

def get_pit_stops(request, intent, previous_intent, CONTEXT):

    CONTEXT['intent'] = 'pit_stops'

    year = None
    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    year = get_variable(request, CONTEXT, 'year', 0, intent)
    if numbers!=None:
        for i in numbers:
            if i>=1000:
                year = i
            else:
                number = i

    top_bottom = get_variable(request, CONTEXT, 'top_bottom', 0, intent)

    if any([i in ['gp_name', 'circuit_name', 'locality', 'country'] for i in request['entities'].keys()]):
        CONTEXT.pop('gp_name', None)
        CONTEXT.pop('circuit_name', None)
        CONTEXT.pop('locality', None)
        CONTEXT.pop('country', None)

    gp_name = get_variable(request, CONTEXT, 'gp_name', 0, intent)
    circuit_name = get_variable(request, CONTEXT, 'circuit_name', 0, intent)
    locality = get_variable(request, CONTEXT, 'locality', 0, intent)
    country = get_variable(request, CONTEXT, 'country', 0, intent)
    driver = get_variable(request, CONTEXT, 'driver', 0, intent)
    constructor = get_variable(request, CONTEXT, 'constructor', 0, intent)
    team_or_driver = get_variable(request, CONTEXT, 'team_or_driver', 0, intent)

    if 'constructor' in request['entities'].keys() or \
            ('team_or_driver' in request['entities'].keys() and \
            request['entities']['team_or_driver'][0]['value']=='team'):
        team_or_driver = 'team'
        driver = None
        CONTEXT.pop('driver', None)

    if 'driver' in request['entities'].keys() or \
            ('team_or_driver' in request['entities'].keys() and \
            request['entities']['team_or_driver'][0]['value']=='driver'):
        team_or_driver = 'driver'
        constructor = None
        CONTEXT.pop('constructor', None)

    #E.g. Who qualified 2nd in monza? And who won the race?
    if 'top_bottom' in request['entities'].keys() \
            and 'driver' not in request['entities'].keys()\
            and 'constructor' in request['entities'].keys():
        driver = None
        constructor = None
        CONTEXT.pop('driver', None)
        CONTEXT.pop('constructor', None)

    y = {'intent':CONTEXT['intent'],
         'year': year,
           'top_bottom': top_bottom,
           'gp_name': gp_name,
           'circuit_name': circuit_name,
           'locality': locality,
           'country': country,
           'driver': driver,
           'constructor': constructor,
           'team_or_driver': team_or_driver}
    CONTEXT = clean_dict(y)
#    z = CONTEXT.copy()
#    z.update(y)
#    CONTEXT = z

    returned_triplets, year, gp_names = \
            pit_stop_times(gp_name, circuit_name, locality, \
            country, year, driver, constructor)

    print (returned_triplets)

    if isinstance(returned_triplets, str) and returned_triplets=='data_NA':
        return random.choice(DATA_NA), CONTEXT

    if len(returned_triplets)==1:
        CONTEXT['constructor'] = returned_triplets[0][1]
        CONTEXT['driver'] = returned_triplets[0][0]

    #Non empty values
    lst = [gp_name, circuit_name, locality, country, year]
    lst = [i for i in lst if i!=None]

    lst_no_gp = [circuit_name, locality, country, year]
    lst_no_gp = [i for i in lst_no_gp if i!=None]

    if len(gp_names)==0:
        text_1 = ["There was no " + tgen.no_such_race_text(lst_no_gp, gp_name) + "."]
    else:
        text_1 = []
        if len(gp_names)>1:
            if gp_name!=None:
                text_1.append("There were " + str(len(gp_names)) + gp_names + "s in " + \
                        ' in '.join([str(i).title() for i in lst]) + ".")
            else:
                text_1.append("There were " + str(len(gp_names)) + " races in " + \
                        ' in '.join([str(i).title() for i in lst_no_gp]) + ".")

        for race_no in range(len(returned_triplets)):
            text_2 = tgen.text_for_pit_stops(returned_triplets[race_no], \
                    gp_names[race_no], driver, constructor, year)
            text_1 = text_1 + text_2

    return text_1, CONTEXT

def get_aggregate_stats(request, intent, previous_intent, CONTEXT):

    CONTEXT['intent'] = 'aggregate_stats'

    #TODO: Improve year detection (e.g. 'year' is not available on the 'request')
    year = None
    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    year = get_variable(request, CONTEXT, 'year', 0, intent)
    if numbers!=None:
        for i in numbers:
            if i>=1000:
                year = i
            else:
                number = i

    podium = get_variable(request, CONTEXT, 'podium', 0, intent)
    top_bottom = get_variable(request, CONTEXT, 'top_bottom', 0, intent)
    if podium=='podium':
        top_bottom = 'top'
        number = 3

    if any([i in ['gp_name', 'circuit_name', 'locality', 'country'] for i in request['entities'].keys()]):
        CONTEXT.pop('gp_name', None)
        CONTEXT.pop('circuit_name', None)
        CONTEXT.pop('locality', None)
        CONTEXT.pop('country', None)

    gp_name = get_variable(request, CONTEXT, 'gp_name', 0, intent)
    circuit_name = get_variable(request, CONTEXT, 'circuit_name', 0, intent)
    locality = get_variable(request, CONTEXT, 'locality', 0, intent)
    country = get_variable(request, CONTEXT, 'country', 0, intent)
    ordinal = get_variable(request, CONTEXT, 'ordinal', 0, intent)
    driver = get_variable(request, CONTEXT, 'driver', 0, intent)
    constructor = get_variable(request, CONTEXT, 'constructor', 0, intent)
    team_or_driver = get_variable(request, CONTEXT, 'team_or_driver', 0, intent)

    if (top_bottom=='top' or ordinal==1):
        podium = None
        CONTEXT.pop('podium', None)

    if 'ordinal' in request['entities'].keys():
        number = None
        top_bottom = None
        CONTEXT.pop('number', None)
        CONTEXT.pop('top_bottom', None)
    elif ('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']<1000) or \
            'podium' in request['entities'].keys() or \
            'top_bottom' in request['entities'].keys() and \
            podium==None:
        ordinal = None
        CONTEXT.pop('ordinal', None)

    if 'top_bottom' in request['entities'].keys() and \
            (('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']>=1000) or \
            ('number' not in request['entities'].keys())):
        number = None
        CONTEXT.pop('number', None)

    if 'constructor' in request['entities'].keys() or \
        'driver' in request['entities'].keys():
        driver = get_variable(request, CONTEXT, 'driver', 0, intent, request_only=True)
        constructor = get_variable(request, CONTEXT, 'constructor', 0, intent, request_only=True)

#    if 'constructor' in request['entities'].keys() or \
#            ('team_or_driver' in request['entities'].keys() and \
#            request['entities']['team_or_driver'][0]['value']=='team'):
#        team_or_driver = 'team'
#        driver = None
#        CONTEXT.pop('driver', None)
#
#    if 'driver' in request['entities'].keys() or \
#            ('team_or_driver' in request['entities'].keys() and \
#            request['entities']['team_or_driver'][0]['value']=='driver'):
#        team_or_driver = 'driver'
#        constructor = None
#        CONTEXT.pop('constructor', None)
#
#    if 'driver' in request['entities'].keys() or 'constructor' in request['entities'].keys():
#        ordinal = None
#        CONTEXT.pop('ordinal', None)

#    #E.g. Who qualified 2nd in monza? And who won the race?
#    if 'top_bottom' in request['entities'].keys() \
#            or ('number' in request['entities'].keys() and request['entities']['number'][0]['value']<1000)\
#            or 'podium' in request['entities'].keys() \
#            or 'ordinal' in request['entities'].keys():
#        driver = None
#        constructor = None
#        CONTEXT.pop('driver', None)
#        CONTEXT.pop('constructor', None)

    y = {'intent':CONTEXT['intent'],
         'year': year,
           'number': [number],
           'podium': podium,
           'top_bottom': top_bottom,
           'gp_name': gp_name,
           'circuit_name': circuit_name,
           'locality': locality,
           'country': country,
           'ordinal': ordinal,
           'driver': driver,
           'constructor': constructor,
           'team_or_driver': team_or_driver}
    CONTEXT = clean_dict(y)
    #z = CONTEXT.copy()
    #z.update(y)
#    CONTEXT = y

    if driver==None and constructor==None:
        text = ["Which driver or team are you talking about?"]
        return text, CONTEXT

    text = ''
    print (gp_name, circuit_name, locality, country, \
                            year, top_bottom, number, ordinal, driver, \
                            constructor, team_or_driver, podium)
    if driver!=None and constructor!=None:
        #TODO: Improve driver-constructor detection
        _, raw_drivers, _ = drivers_of_team(gp_name, \
                    circuit_name, locality, country, year, constructor)
        #print raw_drivers[0]
        if driver not in raw_drivers[0] and year!=None:
            text = tgen.text_driver_not_in_team(driver, constructor)

    if text=='':
        metric_value = aggregate_stats(gp_name, circuit_name, locality, country, \
                        year, top_bottom, number, ordinal, driver, \
                        constructor, podium)

        text = tgen.text_for_aggregate_stats(gp_name, circuit_name, locality, country, \
                        year, top_bottom, number, ordinal, driver, \
                        constructor, team_or_driver, podium, metric_value)

    return text, CONTEXT


def get_most_aggregate_stats(request, intent, previous_intent, CONTEXT):

    CONTEXT['intent'] = 'most_aggregate_stats'

    year = None
    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    year = get_variable(request, CONTEXT, 'year', 0, intent)
    if numbers!=None:
        for i in numbers:
            if i>=1000:
                year = i
            else:
                number = i

    podium = get_variable(request, CONTEXT, 'podium', 0, intent)
    top_bottom = get_variable(request, CONTEXT, 'top_bottom', 0, intent)
    if podium=='podium':
        top_bottom = 'top'
        number = 3

    ##Who has the MOST WINS
    #if len(get_variable(request, CONTEXT, 'top_bottom', 0, get_all=True))>1:
    #    top_bottom = 'top'
    #    number = 1

    if any([i in ['gp_name', 'circuit_name', 'locality', 'country'] for i in request['entities'].keys()]):
        CONTEXT.pop('gp_name', None)
        CONTEXT.pop('circuit_name', None)
        CONTEXT.pop('locality', None)
        CONTEXT.pop('country', None)

    gp_name = get_variable(request, CONTEXT, 'gp_name', 0, intent)
    circuit_name = get_variable(request, CONTEXT, 'circuit_name', 0, intent)
    locality = get_variable(request, CONTEXT, 'locality', 0, intent)
    country = get_variable(request, CONTEXT, 'country', 0, intent)
    ordinal = get_variable(request, CONTEXT, 'ordinal', 0)
    driver = get_variable(request, CONTEXT, 'driver', 0, intent)
    constructor = get_variable(request, CONTEXT, 'constructor', 0, intent)
    team_or_driver = get_variable(request, CONTEXT, 'team_or_driver', 0, intent)

    if 'ordinal' in request['entities'].keys():
        number = None
        top_bottom = None
        CONTEXT.pop('number', None)
        CONTEXT.pop('top_bottom', None)
    elif ('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']<1000) or \
            'podium' in request['entities'].keys() or \
            'top_bottom' in request['entities'].keys():
        ordinal = None
        CONTEXT.pop('ordinal', None)

    if 'top_bottom' in request['entities'].keys() and \
            (('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']>=1000) or \
            ('number' not in request['entities'].keys())) and \
            podium==None:
        number = None
        CONTEXT.pop('number', None)

    if 'constructor' in request['entities'].keys() or \
        'driver' in request['entities'].keys():
        driver = get_variable(request, CONTEXT, 'driver', 0, intent, request_only=True)
        constructor = get_variable(request, CONTEXT, 'constructor', 0, intent, request_only=True)

    if constructor!=None:
        driver=None
        team_or_driver = 'driver'
    if driver!=None:
        constructor = None
        team_or_driver = 'team'

    y = {'intent':CONTEXT['intent'],
         'year': year,
         'number': [number],
         'podium': podium,
           'top_bottom': top_bottom,
           'gp_name': gp_name,
           'circuit_name': circuit_name,
           'locality': locality,
           'country': country,
           'ordinal': ordinal,
           'driver': driver,
           'constructor': constructor,
           'team_or_driver': team_or_driver}
    CONTEXT = clean_dict(y)
#    z = CONTEXT.copy()
#    z.update(y)
#    CONTEXT = y

    print (gp_name, circuit_name, locality, country, year, \
                        team_or_driver, ordinal, podium, \
                        number, top_bottom, driver, constructor)
    metric_value = most_aggregate_stats(gp_name, circuit_name, locality, country, year, \
                        team_or_driver, ordinal, podium, \
                        number, top_bottom, driver, constructor)

    text = tgen.text_for_most_aggregate_stats(gp_name, circuit_name, locality, country, year, \
                        team_or_driver, ordinal, podium, \
                        number, top_bottom, driver, constructor, metric_value)

    return text, CONTEXT

def get_aggregate_quali_stats(request, intent, previous_intent, CONTEXT):

    CONTEXT['intent'] = 'aggregate_quali_stats'

    #TODO: Improve year detection (e.g. 'year' is not available on the 'request')
    year = None
    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    year = get_variable(request, CONTEXT, 'year', 0, intent)
    if numbers!=None:
        for i in numbers:
            if i>=1000:
                year = i
            else:
                number = i

    pole = get_variable(request, CONTEXT, 'pole', 0, intent)
    top_bottom = get_variable(request, CONTEXT, 'top_bottom', 0, intent)
    if pole=='pole':
        top_bottom = 'top'
        number = 1

    if any([i in ['gp_name', 'circuit_name', 'locality', 'country'] for i in request['entities'].keys()]):
        CONTEXT.pop('gp_name', None)
        CONTEXT.pop('circuit_name', None)
        CONTEXT.pop('locality', None)
        CONTEXT.pop('country', None)

    gp_name = get_variable(request, CONTEXT, 'gp_name', 0, intent)
    circuit_name = get_variable(request, CONTEXT, 'circuit_name', 0, intent)
    locality = get_variable(request, CONTEXT, 'locality', 0, intent)
    country = get_variable(request, CONTEXT, 'country', 0, intent)
    ordinal = get_variable(request, CONTEXT, 'ordinal', 0, intent)
    driver = get_variable(request, CONTEXT, 'driver', 0, intent)
    constructor = get_variable(request, CONTEXT, 'constructor', 0, intent)
    team_or_driver = get_variable(request, CONTEXT, 'team_or_driver', 0, intent)

    if 'ordinal' in request['entities'].keys():
        number = None
        top_bottom = None
        CONTEXT.pop('number', None)
        CONTEXT.pop('top_bottom', None)
    elif ('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']<1000) or \
            'pole' in request['entities'].keys() or \
            'top_bottom' in request['entities'].keys() and \
            pole==None:
        ordinal = None
        CONTEXT.pop('ordinal', None)

    if 'top_bottom' in request['entities'].keys() and \
            (('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']>=1000) or \
            ('number' not in request['entities'].keys())):
        number = None
        CONTEXT.pop('number', None)

    if 'constructor' in request['entities'].keys() or \
        'driver' in request['entities'].keys():
        driver = get_variable(request, CONTEXT, 'driver', 0, intent, request_only=True)
        constructor = get_variable(request, CONTEXT, 'constructor', 0, intent, request_only=True)

    y = {'intent':CONTEXT['intent'],
         'year': year,
           'number': [number],
           'top_bottom': top_bottom,
           'gp_name': gp_name,
           'circuit_name': circuit_name,
           'locality': locality,
           'country': country,
           'ordinal': ordinal,
           'driver': driver,
           'constructor': constructor,
           'team_or_driver': team_or_driver}
    CONTEXT = clean_dict(y)
#    z = CONTEXT.copy()
#    z.update(y)
#    CONTEXT = y

    text = ''
    print (gp_name, circuit_name, locality, country, \
                            year, top_bottom, number, ordinal, driver, \
                            constructor, team_or_driver)
    if driver!=None and constructor!=None:
        #TODO: Improve driver-constructor detection
        _, raw_drivers, _ = drivers_of_team(gp_name, \
                    circuit_name, locality, country, year, constructor)
        #print raw_drivers[0]
        if driver not in raw_drivers[0] and year!=None:
            text = tgen.text_driver_not_in_team(driver, constructor)

    if text=='':
        metric_value = aggregate_quali_stats(gp_name, circuit_name, locality, country, \
                        year, top_bottom, number, ordinal, driver, \
                        constructor, pole)

        text = tgen.text_for_aggregate_quali_stats(gp_name, circuit_name, locality, country, \
                        year, top_bottom, number, ordinal, driver, \
                        constructor, team_or_driver, pole, metric_value)

    added_text = ''
    if driver!=None and driver not in get_current_drivers():
        added_text = "I only have full qualifying data from 2003 onwards, " +\
                    "so the results may be misleading."

    return [added_text, text], CONTEXT


def get_most_aggregate_quali_stats(request, intent, previous_intent, CONTEXT):

    CONTEXT['intent'] = 'most_aggregate_quali_stats'

    year = None
    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    year = get_variable(request, CONTEXT, 'year', 0, intent)
    if numbers!=None:
        for i in numbers:
            if i>=1000:
                year = i
            else:
                number = i

    pole = get_variable(request, CONTEXT, 'pole', 0, intent)
    top_bottom = get_variable(request, CONTEXT, 'top_bottom', 0, intent)
    if pole=='pole':
        top_bottom = 'top'
        number = 1

    ##Who has the MOST WINS
    #if len(get_variable(request, CONTEXT, 'top_bottom', 0, get_all=True))>1:
    #    top_bottom = 'top'
    #    number = 1

    if any([i in ['gp_name', 'circuit_name', 'locality', 'country'] for i in request['entities'].keys()]):
        CONTEXT.pop('gp_name', None)
        CONTEXT.pop('circuit_name', None)
        CONTEXT.pop('locality', None)
        CONTEXT.pop('country', None)

    gp_name = get_variable(request, CONTEXT, 'gp_name', 0, intent)
    circuit_name = get_variable(request, CONTEXT, 'circuit_name', 0, intent)
    locality = get_variable(request, CONTEXT, 'locality', 0, intent)
    country = get_variable(request, CONTEXT, 'country', 0, intent)
    ordinal = get_variable(request, CONTEXT, 'ordinal', 0, intent)
    driver = get_variable(request, CONTEXT, 'driver', 0, intent)
    constructor = get_variable(request, CONTEXT, 'constructor', 0, intent)
    team_or_driver = get_variable(request, CONTEXT, 'team_or_driver', 0, intent)

    if 'ordinal' in request['entities'].keys():
        number = None
        top_bottom = None
        CONTEXT.pop('number', None)
        CONTEXT.pop('top_bottom', None)
    elif ('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']<1000) or \
            'pole' in request['entities'].keys() or \
            'top_bottom' in request['entities'].keys():
        ordinal = None
        CONTEXT.pop('ordinal', None)

    if 'top_bottom' in request['entities'].keys() and \
            (('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']>=1000) or \
            ('number' not in request['entities'].keys())) and \
            pole==None:
        number = None
        CONTEXT.pop('number', None)

    if 'constructor' in request['entities'].keys() or \
        'driver' in request['entities'].keys():
        driver = get_variable(request, CONTEXT, 'driver', 0, intent, request_only=True)
        constructor = get_variable(request, CONTEXT, 'constructor', 0, intent, request_only=True)

    if constructor!=None:
        driver=None
        team_or_driver = 'driver'
    if driver!=None:
        constructor = None
        team_or_driver = 'team'

    y = {'intent':CONTEXT['intent'],
         'year': year,
         'number': [number],
           'top_bottom': top_bottom,
           'gp_name': gp_name,
           'circuit_name': circuit_name,
           'locality': locality,
           'country': country,
           'ordinal': ordinal,
           'driver': driver,
           'constructor': constructor,
           'team_or_driver': team_or_driver}
    CONTEXT = clean_dict(y)
#    z = CONTEXT.copy()
#    z.update(y)
#    CONTEXT = y

    print (gp_name, circuit_name, locality, country, year, \
                        team_or_driver, ordinal, \
                        number, top_bottom, driver, constructor)
    metric_value = most_aggregate_quali_stats(gp_name, circuit_name, locality, \
                                        country, year, \
                                        team_or_driver, ordinal, pole, \
                                        number, top_bottom, driver, constructor)

    text = tgen.text_for_most_aggregate_quali_stats(gp_name, circuit_name, \
                                    locality, country, year, \
                                    team_or_driver, ordinal, pole, \
                                    number, top_bottom, driver, constructor, metric_value)

    added_text = "I only have full qualifying data from 2003 onwards, " +\
                    "so the results may be misleading."

    return [added_text, text], CONTEXT


def get_championship_stats(request, intent, previous_intent, CONTEXT):

    CONTEXT['intent'] = 'championship_stats'

    #TODO: Improve year detection (e.g. 'year' is not available on the 'request')
    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    if numbers!=None:
        for i in numbers:
            if i<1000:
                number = i

    #When did Alonso last win the championship? - we have to ignore the 'last'
    top_bottom = get_variable(request, CONTEXT, 'top_bottom', 0, intent, get_all=True)
    if 'top' in top_bottom:
        top_bottom ='top'
    else:
        top_bottom = None

    ordinal = get_variable(request, CONTEXT, 'ordinal', 0, intent)
    driver = get_variable(request, CONTEXT, 'driver', 0, intent)
    constructor = get_variable(request, CONTEXT, 'constructor', 0, intent)

    if 'ordinal' in request['entities'].keys():
        number = None
        top_bottom = None
        CONTEXT.pop('number', None)
        CONTEXT.pop('top_bottom', None)
    elif ('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']<1000) or \
            'top_bottom' in request['entities'].keys():
        ordinal = None
        CONTEXT.pop('ordinal', None)

    if 'top_bottom' in request['entities'].keys() and \
            (('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']>=1000) or \
            ('number' not in request['entities'].keys())):
        number = None
        CONTEXT.pop('number', None)

    if 'constructor' in request['entities'].keys() or \
        'driver' in request['entities'].keys():
        driver = get_variable(request, CONTEXT, 'driver', 0, intent, request_only=True)
        constructor = get_variable(request, CONTEXT, 'constructor', 0, intent, request_only=True)

    y = {'intent':CONTEXT['intent'],
           'number': [number],
           'top_bottom': top_bottom,
           'ordinal': ordinal,
           'driver': driver,
           'constructor': constructor,}
    CONTEXT = clean_dict(y)
#    z = CONTEXT.copy()
#    z.update(y)
#    CONTEXT = y

    metric_value, years = championship_results(top_bottom, number, ordinal, driver, \
                    constructor)

    text = tgen.text_for_championship_stats(top_bottom, number, ordinal, driver, \
                    constructor, metric_value, years)

    return text, CONTEXT

def get_most_championship_stats(request, intent, previous_intent, CONTEXT):
    CONTEXT['intent'] = 'most_championship_stats'

    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    if numbers!=None:
        for i in numbers:
            if i<1000:
                number = i

    top_bottom = get_variable(request, CONTEXT, 'top_bottom', 0, intent)
    ordinal = get_variable(request, CONTEXT, 'ordinal', 0, intent)
    driver = get_variable(request, CONTEXT, 'driver', 0, intent)
    constructor = get_variable(request, CONTEXT, 'constructor', 0, intent)
    team_or_driver = get_variable(request, CONTEXT, 'team_or_driver', 0, intent)

    if 'ordinal' in request['entities'].keys():
        number = None
        top_bottom = None
        CONTEXT.pop('number', None)
        CONTEXT.pop('top_bottom', None)
    elif ('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']<1000) or \
            'podium' in request['entities'].keys() or \
            'top_bottom' in request['entities'].keys():
        ordinal = None
        CONTEXT.pop('ordinal', None)

    if 'top_bottom' in request['entities'].keys() and \
            (('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']>=1000) or \
            ('number' not in request['entities'].keys())):
        number = None
        CONTEXT.pop('number', None)

    if 'constructor' in request['entities'].keys() or \
        'driver' in request['entities'].keys():
        driver = get_variable(request, CONTEXT, 'driver', 0, intent, request_only=True)
        constructor = get_variable(request, CONTEXT, 'constructor', 0, intent, request_only=True)

    if constructor!=None:
        driver=None
        team_or_driver = 'driver'
    if driver!=None:
        constructor = None
        team_or_driver = 'team'

    y = {'intent':CONTEXT['intent'],
         'number': [number],
           'top_bottom': top_bottom,
           'ordinal': ordinal,
           'driver': driver,
           'constructor': constructor,
           'team_or_driver': team_or_driver}
    CONTEXT = clean_dict(y)
#    z = CONTEXT.copy()
#    z.update(y)
#    CONTEXT = y

    metric_value = most_championship_results(top_bottom, number, ordinal,
                              driver, constructor, team_or_driver)

    text = tgen.text_for_most_championship_stats(team_or_driver, ordinal, \
                        number, top_bottom, driver, constructor, \
                        metric_value)

    return text, CONTEXT

def get_appearance_stats(request, intent, previous_intent, CONTEXT):

    CONTEXT['intent'] = 'appearance_stats'

    year = None
    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    year = get_variable(request, CONTEXT, 'year', 0, intent)
    if numbers!=None:
        for i in numbers:
            if i>=1000:
                year = i
            else:
                number = i

    if any([i in ['gp_name', 'circuit_name', 'locality', 'country'] for i in request['entities'].keys()]):
        CONTEXT.pop('gp_name', None)
        CONTEXT.pop('circuit_name', None)
        CONTEXT.pop('locality', None)
        CONTEXT.pop('country', None)

    gp_name = get_variable(request, CONTEXT, 'gp_name', 0, intent)
    circuit_name = get_variable(request, CONTEXT, 'circuit_name', 0, intent)
    locality = get_variable(request, CONTEXT, 'locality', 0, intent)
    country = get_variable(request, CONTEXT, 'country', 0, intent)
    driver = get_variable(request, CONTEXT, 'driver', 0, intent)
    constructor = get_variable(request, CONTEXT, 'constructor', 0, intent)

    if 'constructor' in request['entities'].keys() or \
        'driver' in request['entities'].keys():
        driver = get_variable(request, CONTEXT, 'driver', 0, intent, request_only=True)
        constructor = get_variable(request, CONTEXT, 'constructor', 0, intent, request_only=True)

    y = {'intent':CONTEXT['intent'],
         'year': year,
           'number': [number],
           'gp_name': gp_name,
           'circuit_name': circuit_name,
           'locality': locality,
           'country': country,
           'driver': driver,
           'constructor': constructor}
    CONTEXT = clean_dict(y)

    metric_value = appearances_stats(gp_name, circuit_name, locality, country, year, \
                                    driver, constructor)

    text = tgen.text_for_appearances_stats(gp_name, circuit_name, locality, country, \
                    year, driver, constructor, metric_value)

    return text, CONTEXT

#TODO: Think on how to gather the appropriate data. Now it's only hard-coded values
def get_most_appearance_stats(request, intent, previous_intent, CONTEXT):
    CONTEXT['intent'] = 'most_appearance_stats'

    driver = get_variable(request, CONTEXT, 'driver', 0, intent)
    constructor = get_variable(request, CONTEXT, 'constructor', 0, intent)
    team_or_driver = get_variable(request, CONTEXT, 'team_or_driver', 0, intent)

    if 'constructor' in request['entities'].keys() or \
        'driver' in request['entities'].keys():
        driver = get_variable(request, CONTEXT, 'driver', 0, intent, request_only=True)
        constructor = get_variable(request, CONTEXT, 'constructor', 0, intent, request_only=True)

    if constructor!=None:
        driver=None
        team_or_driver = 'driver'
    if driver!=None:
        constructor = None
        team_or_driver = 'team'

    y = {'intent':CONTEXT['intent'],
           'driver': driver,
           'constructor': constructor,
           'team_or_driver': team_or_driver}
    CONTEXT = clean_dict(y)

#    driver_or_team, times = most_appearance_stats(gp_name, circuit_name, locality, country, year=2016, \
#                        team_or_driver=None, driver=None, constructor=None)

    text = tgen.text_for_most_appearance_stats(team_or_driver)

    return text, CONTEXT

def get_drivers_of_team(request, intent, previous_intent, CONTEXT):
    CONTEXT['intent'] = 'drivers_of_team'

    year = None
    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    year = get_variable(request, CONTEXT, 'year', 0, intent)
    if numbers!=None:
        for i in numbers:
            if i>=1000:
                year = i
            else:
                number = i

    if any([i in ['gp_name', 'circuit_name', 'locality', 'country'] for i in request['entities'].keys()]):
        CONTEXT.pop('gp_name', None)
        CONTEXT.pop('circuit_name', None)
        CONTEXT.pop('locality', None)
        CONTEXT.pop('country', None)

    gp_name = get_variable(request, CONTEXT, 'gp_name', 0, intent)
    circuit_name = get_variable(request, CONTEXT, 'circuit_name', 0, intent)
    locality = get_variable(request, CONTEXT, 'locality', 0, intent)
    country = get_variable(request, CONTEXT, 'country', 0, intent)
    constructor = get_variable(request, CONTEXT, 'constructor', 0, intent)

    y = {'intent':CONTEXT['intent'],
         'year': year,
           'gp_name': gp_name,
           'circuit_name': circuit_name,
           'locality': locality,
           'country': country,
           'constructor': constructor}
    CONTEXT = clean_dict(y)
#    z = CONTEXT.copy()
#    z.update(y)
#    CONTEXT = z

    returned_drivers, raw_drivers, gp_names = drivers_of_team(gp_name, \
                circuit_name, locality, country, year, constructor)

    if isinstance(returned_drivers, str) and returned_drivers=='data_NA':
        return random.choice(DATA_NA), CONTEXT

    #Non empty values
    lst = [gp_name, circuit_name, locality, country, year]
    lst = [i for i in lst if i!=None]

    lst_no_gp = [circuit_name, locality, country, year]
    lst_no_gp = [i for i in lst_no_gp if i!=None]

    if len(gp_names)==0:
        text = "There was no " + tgen.no_such_race_text(lst_no_gp, gp_name) + "."
    else:
        text = ''
        if len(gp_names)>1:
            if gp_name!=None:
                text += "There were " + str(len(gp_names)) + gp_names + "s in " + \
                        ' in '.join([str(i).title() for i in lst]) + "."
            else:
                text += "There were " + str(len(gp_names)) + " races in " + \
                        ' in '.join([str(i).title() for i in lst_no_gp]) + "."

        for race_no in range(len(returned_drivers)):
            if gp_name==None and circuit_name==None and locality==None and country==None:
                text += " "
                text += tgen.text_for_drivers_of_team(returned_drivers[race_no], \
                        gp_names[race_no], constructor, mention_gp_name=False, \
                        year=year)
            else:
                text += " "
                text += tgen.text_for_drivers_of_team(returned_drivers[race_no], \
                        gp_names[race_no], constructor, mention_gp_name=True, \
                        year=year)

    return text, CONTEXT

def get_team_of_driver(request, intent, previous_intent, CONTEXT):
    CONTEXT['intent'] = 'team_of_driver'

    year = None
    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    year = get_variable(request, CONTEXT, 'year', 0, intent)
    if numbers!=None:
        for i in numbers:
            if i>=1000:
                year = i
            else:
                number = i

    if any([i in ['gp_name', 'circuit_name', 'locality', 'country'] for i in request['entities'].keys()]):
        CONTEXT.pop('gp_name', None)
        CONTEXT.pop('circuit_name', None)
        CONTEXT.pop('locality', None)
        CONTEXT.pop('country', None)

    gp_name = get_variable(request, CONTEXT, 'gp_name', 0, intent)
    circuit_name = get_variable(request, CONTEXT, 'circuit_name', 0, intent)
    locality = get_variable(request, CONTEXT, 'locality', 0, intent)
    country = get_variable(request, CONTEXT, 'country', 0, intent)
    driver = get_variable(request, CONTEXT, 'driver', 0, intent)

    y = {'intent':CONTEXT['intent'],
         'year': year,
           'gp_name': gp_name,
           'circuit_name': circuit_name,
           'locality': locality,
           'country': country,
           'driver': driver}
    CONTEXT = clean_dict(y)
#    z = CONTEXT.copy()
#    z.update(y)
#    CONTEXT = z

    returned_constructors, raw_constructors, gp_names = team_of_driver(gp_name, \
                circuit_name, locality, country, year, driver)

    if isinstance(returned_constructors, str) and returned_constructors=='data_NA':
        return random.choice(DATA_NA), CONTEXT

    CONTEXT['constructor'] = raw_constructors[0][0]

    #Non empty values
    lst = [gp_name, circuit_name, locality, country, year]
    lst = [i for i in lst if i!=None]

    lst_no_gp = [circuit_name, locality, country, year]
    lst_no_gp = [i for i in lst_no_gp if i!=None]

    if len(gp_names)==0:
        text = "There was no " + tgen.no_such_race_text(lst_no_gp, gp_name) + "."
    else:
        text = ''
        if len(gp_names)>1:
            if gp_name!=None:
                text += "There were " + str(len(gp_names)) + gp_names + "s in " + \
                        ' in '.join([str(i).title() for i in lst]) + "."
            else:
                text += "There were " + str(len(gp_names)) + " races in " + \
                        ' in '.join([str(i).title() for i in lst_no_gp]) + "."

        for race_no in range(len(returned_constructors)):
            if gp_name==None and circuit_name==None and locality==None and country==None:
                text += " "
                text += tgen.text_for_team_of_driver(returned_constructors[race_no], \
                        gp_names[race_no], driver, mention_gp_name=False, \
                        year=year)
            else:
                text += " "
                text += tgen.text_for_team_of_driver(returned_constructors[race_no], \
                        gp_names[race_no], driver, mention_gp_name=True, \
                        year=year)

    return text, CONTEXT

def get_standings(request, intent, previous_intent, CONTEXT):

    CONTEXT['intent'] = 'standings'

    year = None
    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    year = get_variable(request, CONTEXT, 'year', 0, intent)
    if numbers!=None:
        for i in numbers:
            if i>=1000:
                year = i
            else:
                number = i

    top_bottom = get_variable(request, CONTEXT, 'top_bottom', 0, intent)
    ordinal = get_variable(request, CONTEXT, 'ordinal', 0, intent)
    driver = get_variable(request, CONTEXT, 'driver', 0, intent)
    constructor = get_variable(request, CONTEXT, 'constructor', 0, intent)
    team_or_driver = get_variable(request, CONTEXT, 'team_or_driver', 0, intent)

    if 'ordinal' in request['entities'].keys():
        number = None
        top_bottom = None
        CONTEXT.pop('number', None)
        CONTEXT.pop('top_bottom', None)
    elif ('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']<1000) or \
            'top_bottom' in request['entities'].keys():
        ordinal = None
        CONTEXT.pop('ordinal', None)

    if 'top_bottom' in request['entities'].keys() and \
            (('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']>=1000) or \
            ('number' not in request['entities'].keys())):
        number = None
        CONTEXT.pop('number', None)

    if 'constructor' in request['entities'].keys() or \
            ('team_or_driver' in request['entities'].keys() and \
            request['entities']['team_or_driver'][0]['value']=='team'):
        team_or_driver = 'team'
        driver = None
        CONTEXT.pop('driver', None)

    if 'driver' in request['entities'].keys() or \
            ('team_or_driver' in request['entities'].keys() and \
            request['entities']['team_or_driver'][0]['value']=='driver'):
        team_or_driver = 'driver'
        constructor = None
        CONTEXT.pop('constructor', None)

    if 'driver' in request['entities'].keys() or 'constructor' in request['entities'].keys():
        ordinal = None
        CONTEXT.pop('ordinal', None)

    #E.g. Who qualified 2nd in monza? And who won the race?
    if 'top_bottom' in request['entities'].keys() \
            or ('number' in request['entities'].keys() and request['entities']['number'][0]['value']<1000)\
            or 'ordinal' in request['entities'].keys():
        driver = None
        constructor = None
        CONTEXT.pop('driver', None)
        CONTEXT.pop('constructor', None)

    y = {'intent':CONTEXT['intent'],
         'year': year,
           'number': [number],
           'top_bottom': top_bottom,
           'ordinal': ordinal,
           'driver': driver,
           'constructor': constructor,
           'team_or_driver': team_or_driver}
    CONTEXT = clean_dict(y)
#    z = CONTEXT.copy()
#    z.update(y)
#    CONTEXT = z

    returned_constructors, returned_drivers, returned_positions, \
    raw_constructors, raw_drivers, returned_points, year = \
            standings(year, top_bottom, number, ordinal, driver, \
                    constructor, team_or_driver)

    if isinstance(returned_constructors, str) and returned_constructors=='data_NA':
        return random.choice(DATA_NA), CONTEXT

    #If only fewer drivers took part
    if isinstance(returned_constructors, int):
        text = "There were only " + str(returned_constructors) + " drivers in that championship."
        return text, CONTEXT

    if len(raw_constructors)==1 and raw_constructors[0]:
        CONTEXT['constructor'] = raw_constructors[0]
    if len(raw_drivers)==1 and raw_drivers[0]:
        CONTEXT['driver'] = raw_drivers[0]

    if (team_or_driver=='team' or constructor!=None):
        text = tgen.text_for_standings(returned_constructors, \
                    returned_positions, top_bottom, number, \
                    ordinal, driver, constructor, team_or_driver, year, returned_points)
    else:
        text = tgen.text_for_standings(returned_drivers, \
                    returned_positions, top_bottom, number, \
                    ordinal, driver, constructor, team_or_driver, year, returned_points)

    return text, CONTEXT

def get_race_schedule(request, intent, previous_intent, CONTEXT):
    CONTEXT['intent'] = 'race_schedule'

    CONTEXT.pop('gp_name', None)
    CONTEXT.pop('circuit_name', None)
    CONTEXT.pop('locality', None)
    CONTEXT.pop('country', None)

    #I only get the data from the request, ignoring the context
    gp_name = get_variable(request, CONTEXT, 'gp_name', 0, intent)
    circuit_name = get_variable(request, CONTEXT, 'circuit_name', 0, intent)
    locality = get_variable(request, CONTEXT, 'locality', 0, intent)
    country = get_variable(request, CONTEXT, 'country', 0, intent)

    y = {'intent':CONTEXT['intent'],
         'gp_name': gp_name,
           'circuit_name': circuit_name,
           'locality': locality,
           'country': country}
    CONTEXT = clean_dict(y)
#    z = CONTEXT.copy()
#    z.update(y)
#    CONTEXT = z

    gp_name, race_date, race_time = next_race(gp_name, circuit_name, \
                                    locality, country)

    CONTEXT['circuit_name'] = gp_name

    #Non empty values
    lst = [gp_name, circuit_name, locality, country]
    lst = [i for i in lst if i!=None]

    lst_no_gp = [circuit_name, locality, country]
    lst_no_gp = [i for i in lst_no_gp if i!=None]

    if gp_name==None:
        text = "The schedule for the next race " + tgen.no_such_race_text(lst_no_gp, gp_name) + \
                " has not been published yet."
    else:
        text = tgen.text_for_next_race_schedule(gp_name, race_date, race_time)

    return text, CONTEXT

#TODO: add suggestion to see qualifying results (button yes/no)
def get_free_practice(request, intent, previous_intent, CONTEXT):
    CONTEXT = {}
    CONTEXT['intent'] = 'free_practice'

    year = None
    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    year = get_variable(request, CONTEXT, 'year', 0, intent)
    if numbers!=None:
        for i in numbers:
            if i>=1000:
                year = i
            else:
                number = i

    podium = get_variable(request, CONTEXT, 'podium', 0, intent, request_only=True)
    top_bottom = get_variable(request, CONTEXT, 'top_bottom', 0, intent)
    if podium=='podium':
        top_bottom = 'top'
        number = 3

    if any([i in ['gp_name', 'circuit_name', 'locality', 'country'] for i in request['entities'].keys()]):
        CONTEXT.pop('gp_name', None)
        CONTEXT.pop('circuit_name', None)
        CONTEXT.pop('locality', None)
        CONTEXT.pop('country', None)

    gp_name = get_variable(request, CONTEXT, 'gp_name', 0, intent)
    circuit_name = get_variable(request, CONTEXT, 'circuit_name', 0, intent)
    locality = get_variable(request, CONTEXT, 'locality', 0, intent)
    country = get_variable(request, CONTEXT, 'country', 0, intent)
    ordinal = get_variable(request, CONTEXT, 'ordinal', 0, intent)
    driver = get_variable(request, CONTEXT, 'driver', 0, intent)
    constructor = get_variable(request, CONTEXT, 'constructor', 0, intent)
    team_or_driver = get_variable(request, CONTEXT, 'team_or_driver', 0, intent)

    if 'ordinal' in request['entities'].keys():
        number = None
        top_bottom = None
        CONTEXT.pop('number', None)
        CONTEXT.pop('top_bottom', None)
    elif ('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']<1000) or \
            'podium' in request['entities'].keys() or \
            'top_bottom' in request['entities'].keys():
        ordinal = None
        CONTEXT.pop('ordinal', None)

    if 'top_bottom' in request['entities'].keys() and \
            (('number' in request['entities'].keys() and \
            request['entities']['number'][0]['value']>=1000) or \
            ('number' not in request['entities'].keys())):
        number = None
        CONTEXT.pop('number', None)

    if 'constructor' in request['entities'].keys() or \
            ('team_or_driver' in request['entities'].keys() and \
            request['entities']['team_or_driver'][0]['value']=='team'):
        team_or_driver = 'team'
        driver = None
        CONTEXT.pop('driver', None)

    if 'driver' in request['entities'].keys() or \
            ('team_or_driver' in request['entities'].keys() and \
            request['entities']['team_or_driver'][0]['value']=='driver'):
        team_or_driver = 'driver'
        constructor = None
        CONTEXT.pop('constructor', None)

    if 'driver' in request['entities'].keys() or 'constructor' in request['entities'].keys():
        ordinal = None
        CONTEXT.pop('ordinal', None)

    if 'top_bottom' in request['entities'].keys() \
            or ('number' in request['entities'].keys() and request['entities']['number'][0]['value']<1000)\
            or 'podium' in request['entities'].keys() \
            or 'ordinal' in request['entities'].keys():
        driver = None
        constructor = None
        CONTEXT.pop('driver', None)
        CONTEXT.pop('constructor', None)

    y = {'intent':CONTEXT['intent'],
         'year': year,
           'number': [number],
           'top_bottom': top_bottom,
           'gp_name': gp_name,
           'circuit_name': circuit_name,
           'locality': locality,
           'country': country,
           'ordinal': ordinal,
           'driver': driver,
           'constructor': constructor,
           'team_or_driver': team_or_driver}
    CONTEXT = clean_dict(y)
#    z = CONTEXT.copy()
#    z.update(y)
#    CONTEXT = z

    alternatives = ["I'm sorry but I have no data about the free practice sessions.",
                    "I have not data about the free practice sessions."]

    return random.choice(alternatives), CONTEXT

def get_social_media(request, intent, previous_intent, CONTEXT):
    CONTEXT['intent'] = 'social_media'

    if 'driver' in request['entities'].keys() or \
        'constructor' in request['entities'].keys():
        driver = get_variable(request, CONTEXT, 'driver', 0, intent, request_only=True)
        constructor = get_variable(request, CONTEXT, 'constructor', 0, intent, request_only=True)
    else:
        driver = get_variable(request, CONTEXT, 'driver', 0, intent)
        constructor = get_variable(request, CONTEXT, 'constructor', 0, intent)

    y = {'intent':CONTEXT['intent'],
         'driver': driver,
           'constructor': constructor}
    CONTEXT = clean_dict(y)
#    z = CONTEXT.copy()
#    z.update(y)
#    CONTEXT = z

    tw_account = social_media_accounts(driver, constructor)
    resp = tgen.text_for_social_media(driver, constructor, tw_account)

    return resp, CONTEXT

def get_team_or_driver_comparison(request, intent, previous_intent, CONTEXT):
    CONTEXT = {}
    CONTEXT['intent'] = 'team_or_driver_comparison'

    drivers = get_variable(request, CONTEXT, 'driver', 0, intent, get_all=True, request_only=True)
    constructors = get_variable(request, CONTEXT, 'constructor', 0, intent, get_all=True, request_only=True)

    if drivers==None and constructors==None:
        text = "Please mentions the two drivers or teams you want to compare."
    else:
        if drivers!=None and len(drivers)==1:
            text = "Please mention two driver names you want to compare."
        elif constructors!=None and len(constructors)==1:
            text = "Please mention two teams you want to compare."
        elif drivers!=None and 'alonso' in drivers:
            text = "Fernando Alonso is the best driver ever! He cannot be compared " +\
                    "to anyone!"
        elif drivers!=None and len(drivers)>2:
            drivers = drivers[:2]
            text = ["I can only compare two drivers.",
                    "So, I'm comparing " + tgen.text_for_many_items([driver_mapping[i] for i in drivers]) + "."]
            best, results = compare_drivers_or_teams(drivers, None)
            text.append(tgen.text_for_driver_or_team_comparison(best, results, 'driver'))
        elif constructors!=None and len(constructors)>2:
            constructors = constructors[:2]
            text = ["I can only compare two teams.",
                    "So, I'm comparing " + tgen.text_for_many_items([constuctor_mapping[i] for i in constructors]) + "."]
            best, results = compare_drivers_or_teams(None, constructors)
            text.append(tgen.text_for_driver_or_team_comparison(best, results, 'team'))
        elif drivers!=None and len(drivers)==2:
            best, results = compare_drivers_or_teams(drivers, None)
            text = tgen.text_for_driver_or_team_comparison(best, results, 'driver')
        else:
            best, results = compare_drivers_or_teams(None, constructors)
            text = tgen.text_for_driver_or_team_comparison(best, results, 'team')

    return text, CONTEXT

def get_best_driver_or_team(request, intent, previous_intent, CONTEXT):
    CONTEXT = {}
    CONTEXT['intent'] = 'best_driver_or_team'
    team_or_driver = get_variable(request, CONTEXT, 'team_or_driver', 0, intent)

    if team_or_driver==None:
        team_or_driver = 'driver'

    resp = tgen.text_for_best_driver_or_team(team_or_driver)

    return resp, CONTEXT

def get_play_game(request, intent, previous_intent, CONTEXT):
    CONTEXT['intent'] = 'play_game'
    CONTEXT.pop('number', None)
    num_questions = get_variable(request, CONTEXT, 'number', 0, intent, request_only=True)

    resp, CONTEXT = run_game(request, CONTEXT, num_questions)

    return resp, CONTEXT

def get_teammate(request, intent, previous_intent, CONTEXT):
    CONTEXT['intent'] = 'teammate'

    year = None
    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    year = get_variable(request, CONTEXT, 'year', 0, intent)
    if numbers!=None:
        for i in numbers:
            if i>=1000:
                year = i
            else:
                number = i

    if any([i in ['gp_name', 'circuit_name', 'locality', 'country'] for i in request['entities'].keys()]):
        CONTEXT.pop('gp_name', None)
        CONTEXT.pop('circuit_name', None)
        CONTEXT.pop('locality', None)
        CONTEXT.pop('country', None)

    gp_name = get_variable(request, CONTEXT, 'gp_name', 0, intent)
    circuit_name = get_variable(request, CONTEXT, 'circuit_name', 0, intent)
    locality = get_variable(request, CONTEXT, 'locality', 0, intent)
    country = get_variable(request, CONTEXT, 'country', 0, intent)
    driver = get_variable(request, CONTEXT, 'driver', 0, intent)

    y = {'intent':CONTEXT['intent'],
         'year': year,
           'number': [number],
           'gp_name': gp_name,
           'circuit_name': circuit_name,
           'locality': locality,
           'country': country,
           'driver': driver}
    CONTEXT = clean_dict(y)

    if driver==None:
        text = "Which driver's teammate are you looking for?"
        return text, CONTEXT

    returned_driver, raw_driver, gp_name_new = \
                teammates(gp_name, circuit_name, locality, country, year, driver)

    print (returned_driver, raw_driver, gp_name_new)

    if returned_driver=='data_NA':
        text = tgen.driver_not_racing(gp_name, circuit_name, locality, country, \
                                        year, driver)
        return text, CONTEXT

    #Non empty values
    lst = [gp_name, circuit_name, locality, country, year]
    lst = [i for i in lst if i!=None]

    lst_no_gp = [circuit_name, locality, country, year]
    lst_no_gp = [i for i in lst_no_gp if i!=None]

    print (gp_name, circuit_name, locality, country, year, driver, returned_driver)
    resp = tgen.text_for_teammate(gp_name, circuit_name, locality, country, \
                    year, driver, returned_driver)

    return resp, CONTEXT

def get_driver_or_team_info(request, intent, previous_intent, CONTEXT):
    CONTEXT['intent'] = 'driver_or_team_info'

    if 'driver' in request['entities'].keys() or \
        'constructor' in request['entities'].keys():
        driver = get_variable(request, CONTEXT, 'driver', 0, intent, request_only=True)
        constructor = get_variable(request, CONTEXT, 'constructor', 0, intent, request_only=True)
    else:
        driver = get_variable(request, CONTEXT, 'driver', 0, intent)
        constructor = get_variable(request, CONTEXT, 'constructor', 0, intent)

    y = {'intent':CONTEXT['intent'],
         'driver': driver,
         'constructor' : constructor}
    CONTEXT = clean_dict(y)

    if driver==None and constructor==None:
        text = "For which driver or team are you asking for?"
        return text, CONTEXT

    url, nationality, birthday = \
                driver_or_team_info(driver, constructor)

    resp = tgen.text_for_driver_or_team_info(driver, constructor, url, \
                                            nationality, birthday)
    return resp, CONTEXT

def get_driver_homeland(request, intent, previous_intent, CONTEXT):
    CONTEXT['intent'] = 'driver_homeland'

    if 'driver' in request['entities'].keys(): 
        driver = get_variable(request, CONTEXT, 'driver', 0, intent, request_only=True)
    else:
        driver = get_variable(request, CONTEXT, 'driver', 0, intent)

    y = {'intent':CONTEXT['intent'],
         'driver': driver}
    CONTEXT = clean_dict(y)

    if driver==None:
        text = "For which driver or team are you asking for?"
        return text, CONTEXT

    url, nationality, birthday = \
                driver_homeland(driver)

    resp = tgen.text_for_driver_or_team_info(driver, None, url, \
                                            nationality, birthday)
    return resp, CONTEXT

def get_flags(request, intent, previous_intent, CONTEXT):
    CONTEXT = {}
    CONTEXT['intent'] = 'flags'

    flag_colours_shapes = get_variable(request, CONTEXT, 'flag_colours_shapes', 0, intent, get_all=True)

    flag_description = tgen.text_for_flags(flag_colours_shapes)

    text = "You can find information about the various flags here:"
    element = flags_to_generic()
    resp = {'type':'generic', 'elements':element}

    return [flag_description, text, resp], CONTEXT

#TODO: Find ticket for specific race
def get_ticket(request, intent, previous_intent, CONTEXT):
    CONTEXT['intent'] = 'ticket'

    if any([i in ['gp_name', 'circuit_name', 'locality', 'country'] for i in request['entities'].keys()]):
        CONTEXT.pop('gp_name', None)
        CONTEXT.pop('circuit_name', None)
        CONTEXT.pop('locality', None)
        CONTEXT.pop('country', None)

    gp_name = get_variable(request, CONTEXT, 'gp_name', 0, intent)
    circuit_name = get_variable(request, CONTEXT, 'circuit_name', 0, intent)
    locality = get_variable(request, CONTEXT, 'locality', 0, intent)
    country = get_variable(request, CONTEXT, 'country', 0, intent)

    y = {'intent':CONTEXT['intent'],
           'gp_name': gp_name,
           'circuit_name': circuit_name,
           'locality': locality,
           'country': country}
    CONTEXT = clean_dict(y)

    resp = {}
    resp['type']='button'
    resp['header'] = "You can buy tickets here:"
    resp['buttons_list'] = tickets_button_list()

    return resp, CONTEXT

def get_season_review(request, intent, previous_intent, CONTEXT):
    CONTEXT['intent'] = 'season_review'

    year = None
    number = None
    numbers = get_variable(request, CONTEXT, 'number', 0, intent, get_all=True)
    year = get_variable(request, CONTEXT, 'year', 0, intent)
    if numbers!=None:
        for i in numbers:
            if i>=1000:
                year = i
            else:
                number = i

    y = {'intent':CONTEXT['intent'],
         'year': year}
    CONTEXT = clean_dict(y)

    if year == None or year<1950 or year>2017:
        resp = tgen.no_season_review(year)
    else:
        url = get_season_review_url(year)
        resp = tgen.season_review(year, url)

    return resp, CONTEXT

def get_latest_news(request, intent, previous_intent, CONTEXT):
    CONTEXT = {}
    CONTEXT['intent'] = 'latest_news'

    elements = latest_news_to_generic('news')
    resp = {'type':'generic', 'elements':elements}

    return resp, CONTEXT

def get_latest_videos(request, intent, previous_intent, CONTEXT):
    CONTEXT = {}
    CONTEXT['intent'] = 'latest_videos'

    elements = latest_news_to_generic('videos')
    resp = {'type':'generic', 'elements':elements}

    return resp, CONTEXT

def get_help(request, intent, previous_intent, CONTEXT):
    CONTEXT = {}
    CONTEXT['intent'] = 'help'

    resp = ["You can ask me anything about race and quali results, " +\
            "fastest lap times or quali times and so much more.",
            "You can find sample questions here: www.f1-predictor.com"]

    return resp, CONTEXT


# Setup Actions
actions = {
    'send': send,
    'get_race_or_quali_results': get_race_or_quali_results,
    'get_quali_time' : get_quali_time,
    'get_fastest_lap' : get_fastest_lap,
    'get_aggregate_stats': get_aggregate_stats,
    'get_most_aggregate_stats' : get_most_aggregate_stats,
    'get_aggregate_quali_stats' : get_aggregate_quali_stats,
    'get_most_aggregate_quali_stats' : get_most_aggregate_quali_stats,
    'get_championship_stats' : get_championship_stats,
    'get_most_championship_stats' : get_most_championship_stats,
    'get_appearance_stats' : get_appearance_stats,
    'get_most_appearance_stats': get_most_appearance_stats,
    'get_drivers_of_team' : get_drivers_of_team,
    'get_team_of_driver' : get_team_of_driver,
    'get_pit_stops' : get_pit_stops,
    'get_race_schedule' : get_race_schedule,
    'get_standings' : get_standings,
    'get_free_practice': get_free_practice,
    'get_play_game' : get_play_game,
    'get_latest_news' : get_latest_news,
    'get_latest_videos' : get_latest_videos,
    'get_retirement_reason' : get_retirement_reason,
    'get_retirees' : get_retirees,
    'get_social_media' : get_social_media,
    'get_team_or_driver_comparison' : get_team_or_driver_comparison,
    'get_best_driver_or_team' : get_best_driver_or_team,
    'get_teammate' : get_teammate,
    'get_driver_or_team_info' : get_driver_or_team_info,
    'get_driver_homeland' : get_driver_homeland,
    'get_flags' : get_flags,
    'get_ticket' : get_ticket,
    'get_season_review' : get_season_review,
    'get_god' : get_god,
    'get_help' : get_help
    }

#def handle_response(input_text, audio_url, user_id):
#    return handle_command(input_text, audio_url, user_id)
#    if is_ascii(input_text) or audio_url!='':
#        return handle_command(input_text, audio_url)
#    else:
#        return "Got it!"
#
#def is_ascii(s):
#    return all(ord(c) < 128 for c in s)