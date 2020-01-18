import requests
import json
import sys

FB_PAGE_ACCESS_TOKEN = "EAAaHQsotRuABAMGPl8lemv8rCZBUT00H2GuXuH5VXZA1v4SUhjySU2x0G7UiDYZCdeUu8Rz8k5DneE2VfZCUOjQEiFeKZAOigpHFR3B09txdX7PLtgM8uGCrkm00IvNaFefsZCdSFEU0EF0kUihiL4lUoZAeA23qZB6kVfMXk9WD0QZDZD"

def send_greeting_text():
    log("sending greeting text...")
    params = {
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "setting_type": "greeting",
        "greeting": {
            "text": "Hi {{user_full_name}}, welcome to Formula 1 chatbot!"
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/thread_settings", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
        return True
    else:
        return False

def delete_greeting_text():
    log("deleting greeting text...")
    params = {
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "setting_type": "greeting",
    })
    r = requests.delete("https://graph.facebook.com/v2.6/me/thread_settings", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
        return True
    else:
        return False

def send_get_started():
    log("sending get started button...")
    params = {
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "setting_type": "call_to_actions",
        "thread_state": "new_thread",
        "call_to_actions":[
            {
              "payload":"Get started"
            }
          ]
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/thread_settings", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
        return True
    else:
        return False

def delete_get_started():
    log("deleting get started button...")
    params = {
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "setting_type": "call_to_actions",
        "thread_state": "new_thread",
    })
    r = requests.delete("https://graph.facebook.com/v2.6/me/thread_settings", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
        return True
    else:
        return False

#The URL should be whitelisted first
def send_persistent_menu():
    log("sending persistent menu...")
    params = {
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "setting_type": "call_to_actions",
        "thread_state": "existing_thread",
        "call_to_actions":[
            {
              "type":"postback",
              "title":"Latest news",
              "payload":"Latest news"
            },
            {
              "type":"postback",
              "title":"Latest videos",
              "payload":"Latest videos"
            },
            {
              "type":"postback",
              "title":"Play game",
              "payload":"Play game"
            },
            {
              "type":"postback",
              "title":"Help",
              "payload":"Help"
            }
          ]
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/thread_settings", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
        return True
    else:
        return False

def delete_persistent_menu():
    log("deleting persistent menu...")
    params = {
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "setting_type": "call_to_actions",
        "thread_state": "existing_thread",
    })
    r = requests.delete("https://graph.facebook.com/v2.6/me/thread_settings", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
        return True
    else:
        return False

#The URLs should be HTTPS
def add_whitelisted_url(url_list = ["https://www.f1-predictor.com/", "https://www.formula1.com/"]):
    log("adding whitelisted url...")
    params = {
        "access_token": FB_PAGE_ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "setting_type": "domain_whitelisting",
        "whitelisted_domains" : url_list,
        "domain_action_type": "add"
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/thread_settings", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
        return True
    else:
        return False

def send_generic_buttons(recipient_id, elements):

    log("sending button with to {recipient}".format(recipient=recipient_id))

    params = {
        "access_token": FB_PAGE_ACCESS_TOKEN
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


def log(message):
    print str(message)
    sys.stdout.flush()

if __name__ == "__main__":
    delete_greeting_text()
    delete_get_started()
    delete_persistent_menu()

    add_whitelisted_url(url_list = ["https://www.formula1.com/"])
    send_greeting_text()
    send_get_started()
    send_persistent_menu()