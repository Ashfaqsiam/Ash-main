import datetime
import json
import os
from pipes import quote
import re
import sqlite3
import struct
import subprocess
import time
import webbrowser
import requests 
from playsound import playsound
import eel
import pyaudio
import pyautogui
import pywhatkit as kit
import pvporcupine
import google.generativeai as genai
from groq import Groq

from engine.command import speak
from engine.config import ASSISTANT_NAME, LLM_KEY, GROQ_API_KEY
from engine.helper import extract_yt_term, markdown_to_text, remove_words
from hugchat import hugchat

con = sqlite3.connect("jarvis.db")
cursor = con.cursor()

@eel.expose
def playAssistantSound():
    music_dir = "www\\assets\\audio\\start_sound.mp3"
    playsound(music_dir)

def openCommand(query):
    query = query.replace(ASSISTANT_NAME, "")
    query = query.replace("open", "")
    query.lower()

    app_name = query.strip()

    if app_name != "":
        try:
            cursor.execute(
                'SELECT path FROM sys_command WHERE name IN (?)', (app_name,))
            results = cursor.fetchall()

            if len(results) != 0:
                speak("Opening "+query)
                os.startfile(results[0][0])

            elif len(results) == 0: 
                cursor.execute(
                'SELECT url FROM web_command WHERE name IN (?)', (app_name,))
                results = cursor.fetchall()
                
                if len(results) != 0:
                    speak("Opening "+query)
                    webbrowser.open(results[0][0])
                else:
                    speak("Opening "+query)
                    try:
                        os.system('start '+query)
                    except:
                        speak("not found")
        except:
            speak("some thing went wrong")

def PlayYoutube(query):
    search_term = extract_yt_term(query)
    
    # Check if search_term actually found something
    if search_term is None or search_term.strip() == "":
        # If the user just said "play this on youtube", we look for "national anthem"
        search_term = query.replace("on youtube", "").replace("play", "").replace("this", "").strip()
    
    if search_term:
        speak("Playing " + str(search_term) + " on YouTube")
        kit.playonyt(search_term)
    else:
        speak("I'm sorry, I couldn't figure out which video you wanted to play.")
# --- HOTWORD FUNCTION ---
def hotword(hotword_event=None):
    porcupine=None
    paud=None
    audio_stream=None
    
    # Put your Picovoice Access Key 
    ACCESS_KEY = ""

    # Windows file path
    PPN_FILE_PATH = r"D:\Hello-ASH_en_windows_v4_0_0 (1)\Hello-ASH_en_windows_v4_0_0.ppn" 
    
    try:
        porcupine=pvporcupine.create(
            access_key=ACCESS_KEY, 
            keyword_paths=[PPN_FILE_PATH],
            sensitivities=[0.85]
        ) 
        paud=pyaudio.PyAudio()
        audio_stream=paud.open(rate=porcupine.sample_rate,channels=1,format=pyaudio.paInt16,input=True,frames_per_buffer=porcupine.frame_length)
        
        print("Listening for Hello Ash...")
        
        while True:
            keyword = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            keyword=struct.unpack_from("h"*porcupine.frame_length,keyword)
            keyword_index=porcupine.process(keyword)

            if keyword_index>=0:
                print("hotword detected")
                if hotword_event:
                    hotword_event.set()
                time.sleep(1)
                
    except Exception as e:
        print(f"An error occurred: {e}")
        
    finally:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if paud is not None:
            paud.terminate()

# find contacts
def findContact(query):
    words_to_remove = [ASSISTANT_NAME, 'make', 'a', 'to', 'phone', 'call', 'send', 'message', 'wahtsapp', 'video']
    query = remove_words(query, words_to_remove)

    try:
        query = query.strip().lower()
        cursor.execute("SELECT mobile_no FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?", ('%' + query + '%', query + '%'))
        results = cursor.fetchall()
        print(results[0][0])
        mobile_number_str = str(results[0][0])

        if not mobile_number_str.startswith('+88'):
            mobile_number_str = '+88' + mobile_number_str

        return mobile_number_str, query
    except:
        speak('not exist in contacts')
        return 0, 0
    
def whatsApp(mobile_no, message, flag, name):
    if flag == 'message':
        target_tab = 12
        jarvis_message = "message send successfully to "+name
    elif flag == 'call':
        target_tab = 7
        message = ''
        jarvis_message = "calling to "+name
    else:
        target_tab = 6
        message = ''
        jarvis_message = "staring video call with "+name

    encoded_message = quote(message)
    print(encoded_message)
    whatsapp_url = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"
    full_command = f'start "" "{whatsapp_url}"'

    subprocess.run(full_command, shell=True)
    time.sleep(5)
    subprocess.run(full_command, shell=True)
    
    pyautogui.hotkey('ctrl', 'f')

    for i in range(1, target_tab):
        pyautogui.hotkey('tab')

    pyautogui.hotkey('enter')
    speak(jarvis_message)

# chat bot 
def chatBot(query):
    user_input = query.lower()
    chatbot = hugchat.ChatBot(cookie_path="engine\cookies.json")
    id = chatbot.new_conversation()
    chatbot.change_conversation(id)
    response =  chatbot.chat(user_input)
    print(response)
    speak(response)
    return response

# android automation
def makeCall(name, mobileNo):
    mobileNo =mobileNo.replace(" ", "")
    speak("Calling "+name)
    command = 'adb shell am start -a android.intent.action.CALL -d tel:'+mobileNo
    os.system(command)

# to send message
def sendMessage(message, mobileNo, name):
    from engine.helper import replace_spaces_with_percent_s, goback, keyEvent, tapEvents, adbInput
    message = replace_spaces_with_percent_s(message)
    mobileNo = replace_spaces_with_percent_s(mobileNo)
    speak("sending message")
    goback(4)
    time.sleep(1)
    keyEvent(3)
    tapEvents(136, 2220)
    tapEvents(819, 2192)
    adbInput(mobileNo)
    tapEvents(601, 574)
    tapEvents(390, 2270)
    adbInput(message)
    tapEvents(957, 1397)
    speak("message send successfully to "+name)

# --- THE UNSTOPPABLE HYBRID BRAIN (Gemini 3 -> Groq) ---
def hybrid_ai_brain(query):
    if not query or query.strip() == "":
        return 

    try:
        query = query.replace(ASSISTANT_NAME, "").replace("search", "").strip()
        
        now = datetime.datetime.now()
        current_time = now.strftime("%I:%M %p") 
        current_date = now.strftime("%B %d, %Y") 
        
        persona = ""
        try:
            with open("memory.txt", "r", encoding="utf-8") as file:
                persona = file.read()
            persona = persona.replace("{time}", current_time).replace("{date}", current_date)
        except FileNotFoundError:
            persona = f"Your name is Ash. You were built by Ashfaq Ahamed. Time is {current_time}. Be helpful."

       # ATTEMPT 1: GEMINI 2.5 FLASH
        try:
            print("[Brain] Asking Gemini 2.5 Flash...")
            genai.configure(api_key=LLM_KEY)
            
            # The stable ID is 'gemini-2.5-flash'
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash", 
                system_instruction=persona
            )
            response = model.generate_content(query)
            filter_text = markdown_to_text(response.text)
            
            print(f"Ash (Gemini 2.5) says: {filter_text}") 
            speak(filter_text)
            return

        except Exception as e:
            error_message = str(e).lower()
            if "429" in error_message or "quota" in error_message:
                print("\n[Warning] Gemini hit its limit! Switching to Groq...")
            else:
                print(f"\n[Warning] Gemini failed: {e}. Switching to Groq...")

       # ATTEMPT 2: GROQ
        try:
            print("[Brain] Asking Groq...")
            client = Groq(api_key=GROQ_API_KEY)
            
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant", # <--- NEW, CURRENT MODEL
                messages=[
                    {"role": "system", "content": persona},
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            
            answer = completion.choices[0].message.content
            filter_text = markdown_to_text(answer)
            
            print(f"Ash (Groq) says: {filter_text}") 
            speak(filter_text)
            return

        except Exception as groq_e:
            print(f"Groq Error: {groq_e}")
            speak("Both of my brains are currently out of quota. Please give me a minute.")

    except Exception as main_e:
        print(f"Brain Error: {main_e}")
        speak("A critical error occurred in my brain functions.")

# --- ASH's LEARNING ENGINE ---
def rememberFact(query):
    query = query.replace(ASSISTANT_NAME, "").strip()
    
    if "remember that" in query:
        fact = query.split("remember that")[1].strip()
    elif "remember" in query:
        fact = query.split("remember")[1].strip()
    else:
        speak("What would you like me to remember?")
        return

    if fact != "":
        try:
            with open("memory.txt", "a", encoding="utf-8") as file:
                file.write(f"\n- {fact.capitalize()}.")
            
            print(f"[MEMORY UPDATED]: {fact}")
            speak(f"Got it. I will remember that {fact}.")
        except Exception as e:
            print(f"Memory Error: {e}")
            speak("Sorry, I had trouble writing that down in my memory file.")

# --- Settings Modals ---
@eel.expose
def assistantName():
    name = ASSISTANT_NAME
    return name

@eel.expose
def personalInfo():
    try:
        cursor.execute("SELECT * FROM info")
        results = cursor.fetchall()
        jsonArr = json.dumps(results[0])
        eel.getData(jsonArr)
        return 1    
    except:
        print("no data")

@eel.expose
def updatePersonalInfo(name, designation, mobileno, email, city):
    cursor.execute("SELECT COUNT(*) FROM info")
    count = cursor.fetchone()[0]

    if count > 0:
        cursor.execute(
            '''UPDATE info 
               SET name=?, designation=?, mobileno=?, email=?, city=?''',
            (name, designation, mobileno, email, city)
        )
    else:
        cursor.execute(
            '''INSERT INTO info (name, designation, mobileno, email, city) 
               VALUES (?, ?, ?, ?, ?)''',
            (name, designation, mobileno, email, city)
        )

    con.commit()
    personalInfo()
    return 1

@eel.expose
def displaySysCommand():
    cursor.execute("SELECT * FROM sys_command")
    results = cursor.fetchall()
    jsonArr = json.dumps(results)
    eel.displaySysCommand(jsonArr)
    return 1

@eel.expose
def deleteSysCommand(id):
    cursor.execute("DELETE FROM sys_command WHERE id = ?", (id,))
    con.commit()

@eel.expose
def addSysCommand(key, value):
    cursor.execute(
        '''INSERT INTO sys_command VALUES (?, ?, ?)''', (None,key, value))
    con.commit()

@eel.expose
def displayWebCommand():
    cursor.execute("SELECT * FROM web_command")
    results = cursor.fetchall()
    jsonArr = json.dumps(results)
    eel.displayWebCommand(jsonArr)
    return 1

@eel.expose
def addWebCommand(key, value):
    cursor.execute(
        '''INSERT INTO web_command VALUES (?, ?, ?)''', (None, key, value))
    con.commit()

@eel.expose
def deleteWebCommand(id):
    cursor.execute("DELETE FROM web_command WHERE Id = ?", (id,))
    con.commit()

@eel.expose
def displayPhoneBookCommand():
    cursor.execute("SELECT * FROM contacts")
    results = cursor.fetchall()
    jsonArr = json.dumps(results)
    eel.displayPhoneBookCommand(jsonArr)
    return 1

@eel.expose
def deletePhoneBookCommand(id):
    cursor.execute("DELETE FROM contacts WHERE Id = ?", (id,))
    con.commit()

@eel.expose
def InsertContacts(Name, MobileNo, Email, City):
    cursor.execute(
        '''INSERT INTO contacts VALUES (?, ?, ?, ?, ?)''', (None,Name, MobileNo, Email, City))
    con.commit()