# -*- coding: utf-8 -*-
"""
Created on Tue Feb 21 21:18:09 2017

@author: Stergios
"""

import pandas as pd
import random

import fb_buttons

def possible_answers_to_buttons(question, possible_answers):
    return fb_buttons.create_generic_quick_reply(header=question, lst = possible_answers)


def run_game(request, CONTEXT, num_questions):
    #If the game has NOT started
    if 'questions_asked' not in CONTEXT.keys():
        #If the user has not selected the number of questions to play
        if 'num_questions' not in CONTEXT.keys() and num_questions==None:
            CONTEXT = {}
            CONTEXT['intent'] = 'play_game'
            text = "How many questions do you want to be asked?"
            text = fb_buttons.create_generic_quick_reply(header=text, lst = [1, 2, 3])
            return [text], CONTEXT
        else:
            if num_questions!=None:
                #TODO: Check of num_questions is below, say, 20
                CONTEXT['num_questions'] = num_questions
                CONTEXT['correct_answers'] = 0
                text = "Starting a game with " + str(num_questions) + " questions."
                added_text = "Please select one of the option below each question."
                question, possible_answers, CONTEXT = ask_question(CONTEXT)
                question = possible_answers_to_buttons(question, possible_answers)
                return [text, added_text, question], CONTEXT
            else:
                text = "I didn't get that. How many questions do you want to play?"
                return text, CONTEXT
    else:
        reply = request['_text']
        right_or_wrong_text, CONTEXT = check_last_answer(reply, CONTEXT)

        if len(CONTEXT['questions_asked']) == CONTEXT['num_questions']:
            text = "You correctly answered " + str(CONTEXT['correct_answers']) + \
                " out of " + str(CONTEXT['num_questions']) + " questions!"
            added_text = "Game over!"
            right_or_wrong_text.append(text)
            right_or_wrong_text.append(added_text)
            CONTEXT = {}
            return right_or_wrong_text, CONTEXT
        else:
            question, possible_answers, CONTEXT = ask_question(CONTEXT)
            question = possible_answers_to_buttons(question, possible_answers)
            right_or_wrong_text.append(question)

            return right_or_wrong_text, CONTEXT



def check_last_answer(reply, CONTEXT):
    data = pd.read_csv('game_questions.csv')
    data.set_index(['question_id'], inplace=True)

    previous_question_no = CONTEXT['last_asked_question']
    this_question = data.loc[previous_question_no]

    if this_question['correct_answer'].lower() == reply.lower():
        text = "Correct!"
        added_text = this_question['correct_answer_text']
        CONTEXT['correct_answers'] += 1
    else:
        text = "Wrong!"
        added_text = this_question['wrong_answer_text']

    return [text, added_text], CONTEXT


def ask_question(CONTEXT):
    if 'questions_asked' not in CONTEXT.keys():
        CONTEXT['questions_asked'] = []

    data = pd.read_csv('game_questions.csv')
    data['possible_answers'] = data['possible_answers'].apply(lambda x: x.split(','))
    data.set_index(['question_id'], inplace=True)

    #select question
    q = select_question(data, CONTEXT['questions_asked'])
    CONTEXT['questions_asked'].append(q)
    CONTEXT['last_asked_question'] = q
    this_question = data.loc[q]

    return this_question['question'], this_question['possible_answers'], CONTEXT



def select_question(data, questions_asked):
    q = -1

    started = False
    counter = 0
    while (q in questions_asked and counter<=data.shape[0]) or started==False:
        q = random.randint(1, data.shape[0])
        counter += 1
        started = True

    return q