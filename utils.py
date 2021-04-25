# -*- coding: utf-8 -*-
"""
Created on Sun Jan 15 20:00:22 2017

@author: Stergios
"""

#import thread
import threading
import subprocess
import sys
import urllib3
#import speech_recognition as sr

def clean_dict(y):
    # for key in y.keys():
    #     if y[key]==None or y[key]==[None]:
    #         y.pop(key, None)
            
    return y
    
    
def integer_to_ordinal(value):
    """
    Converts zero or a *positive* integer (or their string 
    representations) to an ordinal value.
    """
    try:
        value = int(value)
    except ValueError:
        return value

    if value % 100//10 != 1:
        if value % 10 == 1:
            ordval = u"%d%s" % (value, "st")
        elif value % 10 == 2:
            ordval = u"%d%s" % (value, "nd")
        elif value % 10 == 3:
            ordval = u"%d%s" % (value, "rd")
        else:
            ordval = u"%d%s" % (value, "th")
    else:
        ordval = u"%d%s" % (value, "th")

    return ordval
    
def proper_language(lang):
    main_sentence = "I'm sorry but I cannot understand "
    if lang=='it':
        main_sentence += "Italian."
    elif lang=='de':
        main_sentence += "German."
    elif lang=='fr':
        main_sentence += "French."
    elif lang=='es':
        main_sentence += "Spanish."
    elif lang=='el':
        main_sentence += "Greek."
    else:
        main_sentence = "I'm sorry but I can only understand English."
        
    return main_sentence

#The two functions below are taking care of a long running script
def cdquit(fn_name):
    print (str(fn_name) + ' took too long.')
    sys.stderr.flush()
    thread.interrupt_main() # raises KeyboardInterrupt

def exit_after(s):
    '''
    use as decorator to exit process if
    function takes longer than s seconds
    '''
    def outer(fn):
        def inner(*args, **kwargs):
            timer = threading.Timer(s, cdquit, args=[fn.__name__])
            timer.start()
            try:
                result = fn(*args, **kwargs)
            finally:
                timer.cancel()
            return result
        return inner
    return outer
        
#Exit the function after 10 seconds have passed
@exit_after(10)
def audio_to_text(audio_url):

    mp4file = urllib2.urlopen(audio_url)
    with open('/home/asstergi/mysite/test.mp4', 'wb') as handle:
        handle.write(mp4file.read())

    cmdline = ['avconv',
               '-loglevel',
               'quiet',
               '-i',
               '/home/asstergi/mysite/test.mp4',
               '-vn',
               '-f',
               'wav',
               '/home/asstergi/mysite/test.wav']
    subprocess.call(cmdline)

    try:
        r = sr.Recognizer()
        with sr.AudioFile('/home/asstergi/mysite/test.wav') as source:
            audio = r.record(source)

        command = r.recognize_google(audio)
    except sr.UnknownValueError:
        command = ''

    print ("DEBUG The command was: ", str(command))
    sys.stdout.flush()

    return command