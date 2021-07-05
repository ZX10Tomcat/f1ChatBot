import sys
import json
import os

import requests
import logging

from flask import Flask, request
#from flask_sslify import SSLify

from handle_input import handle_command
from fb_buttons import create_getting_started_quick_reply
from f1com_stuff import latest_news_to_generic

app = Flask(__name__)
#sslify = SSLify(app)

f=open("appsettings/tokens.txt","r")
lines=f.read().split('\n')
ACCESS_TOKEN=lines[0]
VERIFY_TOKEN=lines[1]
f.close()

@app.route('/', methods=['GET'])
def hello():
    #return "Hello"
    message_text = request.args.get("message")
    try:                    
        print(message_text)

        sender_id= 1 #should be something at least

        resps = handle_command(message_text, "audio_url", sender_id)
        #resps = ["Ha"]
        log(resps)
        return ' '.join(resps), 200
        #send_responses(sender_id, resps)

    #TODO: Change this to show a more user-friendly message
    except Exception:
        logging.exception("message")
        send_message(sender_id, "Sorry, something went wrong.")


@app.route('/webhook', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/webhook', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events
    print ("message incomung!")
    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    try:
                        sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                        recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID

                        if messaging_event["message"].get("text"):
                            message_text = messaging_event["message"]["text"]  # the message's text
                        else:
                            message_text = ''
                        
                        print(message_text)

                        if messaging_event["message"].get("attachments"):
                            if messaging_event["message"]["attachments"][0]['type']=='audio':
                                audio_url = messaging_event["message"]["attachments"][0]['payload']['url']
                        else:
                            audio_url = ''

                        send_sender_action(sender_id) #Informs the user that the bot is doing something
                        resps = handle_command(message_text, audio_url, sender_id)
                        #resps = ["Ha"]
                        log(resps)
                        send_responses(sender_id, resps)

                    #TODO: Change this to show a more user-friendly message
                    except Exception:
                        logging.exception("message")
                        send_message(sender_id, "Sorry, something went wrong.")

                    #Delete audio files if they exist
                    if os.path.exists("/home/asstergi/mysite/test.mp4"):
                        os.remove("/home/asstergi/mysite/test.mp4")
                    if os.path.exists("/home/asstergi/mysite/test.wav"):
                        os.remove("/home/asstergi/mysite/test.wav")

                    else:
                        pass

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    try:
                        sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                        recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                        payload = messaging_event["postback"]["payload"]  # the message's text

                        send_sender_action(sender_id) #Informs the user that the bot is doing something
                        if payload=='Get started':
                            getting_started_quick_reply = create_getting_started_quick_reply("What do you want to do first?")
                            resps = ["Welcome to the Formula 1 chatbot!", \
                                    "I can answer many questions about Formula 1 statistics.", \
                                    "If you want to see what I can do, just type 'help' " + \
                                    "or use the menu on the lower left part of your screen!",
                                    getting_started_quick_reply]
                        else:
                            resps = handle_command(payload, '', sender_id)

                        send_responses(sender_id, resps)

                    #TODO: Change this to show a more user-friendly message
                    except Exception:
                        print ("Unexpected error:")
                        print (sys.exc_info())
                        send_message(sender_id, "Hehe")

    return "ok", 200

def send_responses(sender_id, resps):
    for resp in resps:
        if isinstance(resp, str) or isinstance(resp, unicode):
            if resp=='' or resp==None:
                next
            else:
                error_found = send_message(sender_id, resp)
        elif isinstance(resp, dict):
            if resp['type']=='button':
                error_found = send_buttons(sender_id, resp['header'], resp['buttons_list'])
            elif resp['type']=='quick_reply':
                error_found = send_quick_reply(sender_id, resp['header'], resp['buttons_list'])
            elif resp['type']=='image_or_video':
                error_found = send_image_or_video(sender_id, resp['image_or_video'], resp['url'])
            elif resp['type']=='generic':
                error_found = send_generic_buttons(sender_id, resp['elements'])

    if error_found:
        send_message(sender_id, "Oops, some error occurred! Please try again.")

def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
        return True
    else:
        return False

def send_buttons(recipient_id, header, buttons_list):
    buttons = create_buttons_dict(buttons_list)

    log("sending button with {header} to {recipient}: {buttons}".format(recipient=recipient_id, header=header, buttons = buttons))

    params = {
        "access_token": ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type" : "template",
                "payload":{
                    "template_type":"button",
                    "text":header,
                    "buttons":buttons
                  }
                }
            }
        })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
        return True
    else:
        return False


def send_quick_reply(recipient_id, header, buttons_list):
    quick_replies = create_quick_replies_dict(buttons_list)

    log("sending quick reply with {header} to {recipient}: {quick_replies}".format(recipient=recipient_id, header=header, quick_replies=quick_replies))

    params = {
        "access_token": ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text":header,
                "quick_replies":quick_replies
              }
        })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
        return True
    else:
        return False

def send_sender_action(sender_id):
    log("sending sender_action to {recipient}".format(recipient=sender_id))

    params = {
        "access_token": ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": sender_id
        },
        "sender_action":"typing_on"
        })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def send_image_or_video(recipient_id, image_or_video, url):
    log("sending {image_or_video} to {recipient}: {text}".format(image_or_video=image_or_video, recipient=recipient_id, text=url))

    params = {
        "access_token": ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment":{
              "type":image_or_video,
              "payload":{
                "url":url
              }
            }
          }

    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
        return True
    else:
        return False

def create_buttons_dict(buttons_list):
    buttons = []
    for button in buttons_list:
        this_button = {}

        this_button['type'] = button[0]
        this_button['title'] = button[1]

        if button[0]=="web_url":
            this_button['url'] = button[2]
        elif button[0]=="postback":
            this_button['payload'] = button[2]

        buttons.append(this_button)
    return buttons

def create_quick_replies_dict(buttons_list):
    buttons = []
    for button in buttons_list:
        this_button = {}
        this_button["content_type"] = "text"
        this_button["title"] = button[0]
        this_button["payload"] = button[1]

        if len(button)==3:
            this_button["image_url"] = button[2]

        buttons.append(this_button)
    return buttons

def send_generic_buttons(recipient_id, elements):

    log("sending button with to {recipient}".format(recipient=recipient_id))

    params = {
        "access_token": ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type" : "template",
                "payload":{
                    "template_type":"generic",
                    "elements": elements
                  }
                }
            }
        })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
        return True
    else:
        return False

def log(message):  # simple wrapper for logging to stdout on heroku
    print (str(message))
    sys.stdout.flush()
