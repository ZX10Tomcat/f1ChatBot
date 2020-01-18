# -*- coding: utf-8 -*-
"""
Created on Tue Jan 03 15:45:09 2017

@author: asterios
"""

from slackclient import SlackClient

import random
from retrying import retry
import time

from handle_input import handle_command, WTF


SLACK_BOT_TOKEN='XXX'
BOT_ID = "XXX"

# constants
AT_BOT = "<@" + BOT_ID + ">"

# instantiate Slack & Twilio clients
slack_client = SlackClient(SLACK_BOT_TOKEN)



def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        This parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    try:
        output_list = slack_rtm_output
        if output_list and len(output_list) > 0:
            for output in output_list:
                #print output
                if output and 'text' in output and output['user']!=BOT_ID  \
                    and (output['channel']=='C3RBGP9KK' \
                    or output['channel']=='G3RS9BS72' or output['channel']=="G3B6WCT8W"
                    or output['channel']=='C3G5XCV8U'): #and AT_BOT in output['text']:

                    try:
                        return str(output['text']).strip().lower(), \
                               output['channel'], output['user']
                    except Exception:
                        return output['text'].strip().lower(), \
                               output['channel'], output['user']
        return None, None, None
    except Exception:
        return None, None, None

def send_responses(resps, channel):
    for resp in resps:
        if isinstance(resp, str) or isinstance(resp, unicode):
            if resp=='':
                next
            else:
                slack_client.api_call("chat.postMessage", channel=channel,
                          text=resp, as_user=True)
        elif isinstance(resp, dict):
            if resp['type']=='button':
                slack_client.api_call("chat.postMessage", channel=channel,
                          text=resp['header'], as_user=True)
                slack_client.api_call("chat.postMessage", channel=channel,
                          text=resp['buttons_list'], as_user=True)
            elif resp['type']=='quick_reply':
                slack_client.api_call("chat.postMessage", channel=channel,
                          text=resp['header'], as_user=True)
                slack_client.api_call("chat.postMessage", channel=channel,
                          text=resp['buttons_list'], as_user=True)
            elif resp['type']=='image_or_video':
                slack_client.api_call("chat.postMessage", channel=channel,
                          text=resp['url'], as_user=True)
            elif resp['type']=='generic':
                for i in resp['elements']:
                    slack_client.api_call("chat.postMessage", channel=channel,
                          text=i['buttons'][0]['url'], as_user=True)


@retry
def main():
    #sc = SlackClient(SLACK_BOT_TOKEN)
    #slack_user_list = sc.api_call("users.list")

    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("F1 bot connected and running!")
        while True:

            command, channel, user = parse_slack_output(slack_client.rtm_read())

            if command and channel:
                try:
                    resps = handle_command(command, '', user)
                    send_responses(resps, channel)
                    #resp = handle_command(command, user, slack_user_list)
                    print "--------------OK--------------"
                except Exception:
                    resp = random.choice(WTF)
                    slack_client.api_call("chat.postMessage", channel=channel,
                          text=resp, as_user=True)
            time.sleep(READ_WEBSOCKET_DELAY)

    else:
        print("Connection failed. Invalid Slack token or bot ID?")

if __name__ == "__main__":
    main()