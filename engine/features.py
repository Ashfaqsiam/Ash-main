import datetime
import json
import os
from pipes import quote
import re
import sqlite3
import subprocess
import time
import webbrowser
import requests 
import threading
import socket  # NEW: Required for the internet check
from playsound import playsound
import eel
import pyautogui
import pyaudio
from vosk import Model, KaldiRecognizer 
import google.generativeai as genai
from groq import Groq

# --- NEW VISION IMPORTS ---
import cv2
from PIL import Image



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
    query = query.lower()

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
    
    if search_term is None or search_term.strip() == "":
        search_term = query.replace("on youtube", "").replace("play", "").replace("this", "").strip()
    
    if search_term:
        if is_online():
            speak("Playing " + str(search_term) + " on YouTube")
            # We import it HERE so it doesn't crash the app on startup when offline
            import pywhatkit as kit
            kit.playonyt(search_term)
        else:
            speak("Sir, the system is offline. I cannot connect to YouTube right now.")
    else:
        speak("I'm sorry, I couldn't figure out which video you wanted to play.")
# ==========================================
# --- VOSK ENGINE (100% Free & Offline) ---
# ==========================================
def hotword(hotword_event=None):
    print("\n[DEBUG] 1. Starting Vosk Offline Engine...")
    model_path = r"D:\model\model" 
    
    if not os.path.exists(model_path):
        print(f"\n[CRITICAL ERROR] Could not find Vosk model at {model_path}")
        return

    try:
        print("[DEBUG] 2. Loading Offline Language Model...")
        model = Model(model_path)
        recognizer = KaldiRecognizer(model, 16000, '["hello", "ash", "yash", "wake", "up", "[unk]"]')
        
        print("[DEBUG] 3. Opening Microphone...")
        paud = pyaudio.PyAudio()
        audio_stream = paud.open(
            format=pyaudio.paInt16, 
            channels=1, 
            rate=16000, 
            input=True, 
            frames_per_buffer=8000
        )
        audio_stream.start_stream()
        
        print("\n[HOTWORD PROCESS] Active and listening completely offline...")
        
        while True:
            data = audio_stream.read(4000, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                word = result.get("text", "")
                
                if "hello ash" in word or "hello yash" in word or "wake up" in word:
                    print(f"\n[HOTWORD] >>> DETECTED: '{word}' <<<")
                    if hotword_event:
                        hotword_event.set()
                    time.sleep(8)
                    
    except Exception as e:
        print(f"\n[CRITICAL ERROR IN VOSK]: {e}")
    finally:
        try:
            audio_stream.stop_stream()
            audio_stream.close()
            paud.terminate()
        except:
            pass

def findContact(query):
    words_to_remove = [ASSISTANT_NAME, 'make', 'a', 'to', 'phone', 'call', 'send', 'message', 'wahtsapp', 'video']
    query = remove_words(query, words_to_remove)

    try:
        query = query.strip().lower()
        cursor.execute("SELECT mobile_no FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?", ('%' + query + '%', query + '%'))
        results = cursor.fetchall()
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
        jarvis_message = "starting video call with "+name

    encoded_message = quote(message)
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

def chatBot(query):
    user_input = query.lower()
    chatbot = hugchat.ChatBot(cookie_path="engine\cookies.json")
    id = chatbot.new_conversation()
    chatbot.change_conversation(id)
    response =  chatbot.chat(user_input)
    speak(response)
    return response

def makeCall(name, mobileNo):
    mobileNo = mobileNo.replace(" ", "")
    speak("Calling "+name)
    command = 'adb shell am start -a android.intent.action.CALL -d tel:'+mobileNo
    os.system(command)

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

# ====================================================================
# --- OFFLINE/ONLINE ROUTING PROTOCOLS ---
# ====================================================================

def is_online():
    """Returns True if the computer has internet access, False otherwise."""
    try:
        # Pings Cloudflare's DNS server to verify real internet connectivity
        socket.create_connection(("1.1.1.1", 53), timeout=1.5)
        return True
    except OSError:
        return False

def ask_ollama(prompt, persona):
    """Sends the prompt to your local Ollama server running Llama 3."""
    url = "http://localhost:11434/api/generate"
    
    # 1. Force the AI to be concise. Less text generated = Much faster response time.
    speed_persona = persona + " IMPORTANT: Keep your answers extremely brief, direct, and conversational. 1 to 2 sentences maximum. Do not generate lists or essays."
    
    payload = {
        "model": "llama3", 
        "prompt": prompt,
        "system": speed_persona,
        "stream": False,
        "keep_alive": "1h", # 2. Keeps the model loaded in RAM for 1 hour so it responds instantly next time
        "options": {
            "num_ctx": 1024,     # 3. Limits the "reading" memory to speed up processing
            "num_predict": 100   # 4. Hard-caps the output to ~100 tokens so it never writes an essay
        }
    }
    
    try:
        print("[DEBUG] Sending optimized request to Local Brain...")
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        return data['response']
        
    except requests.exceptions.ConnectionError:
        return "Sir, I am offline, and my local Ollama server is not running in the background."
    except Exception as e:
        print(f"[Ollama Error] {e}")
        return "I encountered an error while trying to access my local brain."


def hybrid_ai_brain(query):
    """The master brain router. Cloud -> Groq -> Local Ollama"""
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

        # =======================================
        # --- ONLINE MODE (Gemini / Groq) ---
        # =======================================
        if is_online():
            # ATTEMPT 1: GEMINI
            try:
                print("[Brain] Internet Detected. Asking Gemini 2.5 Flash...")
                genai.configure(api_key=LLM_KEY)
                model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=persona)
                response = model.generate_content(query)
                filter_text = markdown_to_text(response.text)
                print(f"Ash (Gemini 2.5) says: {filter_text}") 
                speak(filter_text)
                return

            except Exception as e:
                # --- SILENT FAILOVER ---
                print(f"\n[Warning] Gemini API hit a limit or failed. Silently routing to Groq...")

            # ATTEMPT 2: GROQ
            try:
                print("[Brain] Asking Groq...")
                client = Groq(api_key=GROQ_API_KEY)
                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "system", "content": persona}, {"role": "user", "content": query}],
                    temperature=0.7,
                    max_tokens=1024,
                )
                answer = completion.choices[0].message.content
                filter_text = markdown_to_text(answer)
                print(f"Ash (Groq) says: {filter_text}") 
                speak(filter_text)
                return

            except Exception as groq_e:
                speak("Both of my primary cloud networks are currently offline.")

        # =======================================
        # --- OFFLINE MODE (Local Ollama) ---
        # =======================================
        else:
            print("[Brain] No Internet! Routing to Local Brain (Ollama Llama 3)...")
            speak("Network connection lost. Booting local neural network.")
            
            fallback_response = ask_ollama(query, persona)
            filter_text = markdown_to_text(fallback_response)
            
            print(f"Ash (Local Llama 3) says: {filter_text}")
            speak(filter_text)

    except Exception as main_e:
        speak("A critical error occurred in my brain functions.")

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
            speak(f"Got it. I will remember that {fact}.")
        except Exception:
            speak("Sorry, I had trouble writing that down.")

# ====================================================================
# --- SETTINGS MODALS (Renamed Python side to avoid naming collisions) ---
# ====================================================================

@eel.expose
def assistantName():
    return ASSISTANT_NAME

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
        cursor.execute('''UPDATE info SET name=?, designation=?, mobileno=?, email=?, city=?''',
            (name, designation, mobileno, email, city))
    else:
        cursor.execute('''INSERT INTO info (name, designation, mobileno, email, city) VALUES (?, ?, ?, ?, ?)''',
            (name, designation, mobileno, email, city))
    con.commit()
    personalInfo()
    return 1

@eel.expose
def fetchSysCommand():
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
    cursor.execute('''INSERT INTO sys_command VALUES (?, ?, ?)''', (None, key, value))
    con.commit()

@eel.expose
def fetchWebCommand():
    cursor.execute("SELECT * FROM web_command")
    results = cursor.fetchall()
    jsonArr = json.dumps(results)
    eel.displayWebCommand(jsonArr)
    return 1

@eel.expose
def addWebCommand(key, value):
    cursor.execute('''INSERT INTO web_command VALUES (?, ?, ?)''', (None, key, value))
    con.commit()

@eel.expose
def deleteWebCommand(id):
    cursor.execute("DELETE FROM web_command WHERE Id = ?", (id,))
    con.commit()

@eel.expose
def fetchPhoneBook():
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
    cursor.execute('''INSERT INTO contacts VALUES (?, ?, ?, ?, ?)''', (None, Name, MobileNo, Email, City))
    con.commit()

# ==========================================
# --- ASH VISION SYSTEM (Memory-Only Mode) ---
# ==========================================
def ash_vision(query):
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release() 
    
    if not ret:
        speak("Camera error.")
        return

    print("[VISION] Snapped and analyzing in memory...")
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb_frame)
    
    try:
        genai.configure(api_key=LLM_KEY)
        
        smart_instruction = """
        You are Ash, an advanced AI assistant. The user is showing you an image. 
        1. If they simply ask "what is this", identify the main object in one short sentence.
        2. If they ask for specific details (like nutrition, specs, price, or history), act as an expert analyst. Provide a highly concise, factual breakdown. 
        Do not use filler words like "I can see" or "This is a". Just deliver the data directly.
        """
        
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=smart_instruction
        )
        
        if query.strip() in ["what is this", "look at this", "what am i holding"]:
            vision_prompt = "Identify the primary object."
        else:
            vision_prompt = query
            
        response = model.generate_content([vision_prompt, img])
        
        filter_text = markdown_to_text(response.text)
        print(f"Ash (Vision) says: {filter_text}")
        speak(filter_text)
        
    except Exception as e:
        print(f"[VISION ERROR]: {e}")
        speak("Sir, my optical sensors are currently offline due to quota limits or network errors.")

# ==========================================
# --- ASH ALARM SYSTEM (Bulletproof Native) ---
# ==========================================
def set_alarm(time_string):
    """Uses PyAutoGUI to physically set an alarm with higher reliability"""
    speak(f"Preparing to set a permanent alarm for {time_string}.")
    
    try:
        # 1. Open the Windows Run dialog (Win + R)
        pyautogui.hotkey('win', 'r')
        time.sleep(0.5)
        
        # 2. Type the command to open the Windows Clock app
        pyautogui.write('explorer shell:Appsfolder\\Microsoft.WindowsAlarms_8wekyb3d8bbwe!App')
        time.sleep(0.5)
        pyautogui.press('enter')
        
        speak("Opening Windows Alarms. Please do not touch the mouse or keyboard.")
        
        # 3. Wait longer for the app to load fully
        time.sleep(4)
        
        # Maximize the window to ensure the UI is consistent
        pyautogui.hotkey('win', 'up')
        time.sleep(1)
        
        # 4. Press 'Ctrl + N' to add a new alarm
        pyautogui.hotkey('ctrl', 'n')
        time.sleep(1.5) # Wait for the 'New Alarm' animation to finish
        
        # 5. Clean and parse the time
        clean_time = time_string.replace(".", "").strip().lower()
        if ":" not in clean_time:
            if "am" in clean_time:
                clean_time = clean_time.replace("am", ":00 am").strip()
            elif "pm" in clean_time:
                clean_time = clean_time.replace("pm", ":00 pm").strip()
                
        parts = clean_time.replace("am", "").replace("pm", "").strip().split(":")
        
        # Pad with zeros so "2" becomes "02", which types much better in the app
        hour = parts[0].zfill(2) 
        minute = parts[1].zfill(2) if len(parts) > 1 else "00"
        
        # 6. Execute the typing sequence (with slight delays between keystrokes)
        pyautogui.write(hour, interval=0.1)
        time.sleep(0.5)
        
        pyautogui.press('tab')
        time.sleep(0.5)
        
        pyautogui.write(minute, interval=0.1)
        time.sleep(0.5)
        
        # Only tab to AM/PM if the user specified it (respects 24hr clocks)
        if "am" in clean_time or "pm" in clean_time:
            pyautogui.press('tab')
            time.sleep(0.5)
            # Pressing 'a' or 'p' is much safer than the up/down arrows
            if "am" in clean_time:
                pyautogui.press('a')
            else:
                pyautogui.press('p')
                
        time.sleep(1)
        
        # 7. Save the alarm (Try both Ctrl+S and Enter to be absolutely sure)
        pyautogui.hotkey('ctrl', 's')
        time.sleep(0.5)
        pyautogui.press('enter')
        
        # Close the clock app so it doesn't clutter your screen
        time.sleep(1)
        pyautogui.hotkey('alt', 'f4')
        
        speak(f"Permanent alarm successfully saved for {clean_time}.")
        
    except Exception as e:
        print(f"Alarm Error: {e}")
        speak("I encountered an error while trying to operate the Windows Alarm app.")