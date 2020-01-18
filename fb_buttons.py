# -*- coding: utf-8 -*-
"""
Created on Sun Feb 26 12:29:57 2017

@author: Stergios
"""

import requests

def create_yes_no_quick_reply(header):
    buttons_list = [("Yes", "Yes", "http://oi64.tinypic.com/25qcbjp.jpg"),
                    ("No", "No", "http://oi68.tinypic.com/6r4oew.jpg")]
    yes_no_quick_reply = {'type':'quick_reply',
                          'header': header,
                          'buttons_list': buttons_list}
    return yes_no_quick_reply

def create_getting_started_quick_reply(header):
    lst = ["Play game", "Latest news", "Latest videos", "Help"]
    return create_generic_quick_reply(header, lst)

def create_generic_quick_reply(header, lst):
    buttons_list = []
    for item in lst:
        if isinstance(item, str) or isinstance(item, unicode) or isinstance(item, int):
            buttons_list.append((item, item))
        elif isinstance(item, tuple):
            buttons_list.append((item[0], item[0], item[1]))
    quick_reply = {'type':'quick_reply',
                          'header': header,
                          'buttons_list': buttons_list}
    return quick_reply

def create_help_quick_reply(header):
    buttons_list = [("Help", "Help", "http://oi63.tinypic.com/1zwlmk8.jpg")]
    help_quick_reply = {'type':'quick_reply',
                          'header': header,
                          'buttons_list': buttons_list}
    return help_quick_reply


def create_image_or_video_fb_format(image_or_video, url):
    send_image_or_video = {'type':'image_or_video',
                           'image_or_video': image_or_video,
                          'url': url}
    return send_image_or_video


def get_username_from_id(user_id):
    params = {
        "access_token": "EAAaHQsotRuABAMGPl8lemv8rCZBUT00H2GuXuH5VXZA1v4SUhjySU2x0G7UiDYZCdeUu8Rz8k5DneE2VfZCUOjQEiFeKZAOigpHFR3B09txdX7PLtgM8uGCrkm00IvNaFefsZCdSFEU0EF0kUihiL4lUoZAeA23qZB6kVfMXk9WD0QZDZD"
    }
    headers = {
        "Content-Type": "application/json"
    }
    r = requests.get("https://graph.facebook.com/v2.6/" + str(user_id) + "?fields=first_name,last_name", \
                    params=params, headers=headers)

    first_name, last_name = None, None
    if r.status_code == 200:
        first_name = r.json()['first_name'].encode('utf-8')
        last_name = r.json()['last_name'].encode('utf-8')

    return first_name