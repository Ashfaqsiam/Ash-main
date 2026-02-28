import pyttsx3
import speech_recognition as sr
import eel
import time
import threading 
import pygetwindow as gw

# --- Global flag and Engine Initialization ---
stop_speaking_flag = False
speak_lock = threading.Lock()

engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices') 
engine.setProperty('voice', voices[0].id)
engine.setProperty('rate', 174)

def onWord(name, location, length):
    global stop_speaking_flag
    if stop_speaking_flag:
        engine.stop()

engine.connect('started-word', onWord)

def speak(text):
    global stop_speaking_flag
    stop_speaking_flag = False 
    
    with speak_lock:
        try:
            text = str(text)
            eel.DisplayMessage(text)
            eel.receiverText(text)
            
            if getattr(engine, '_in_loop', False):
                engine.say(text)
            else:
                engine.say(text)
                engine.runAndWait()
        except Exception as e:
            print(f"Speak Error: {e}")

def stop_speaking():
    global stop_speaking_flag
    stop_speaking_flag = True
    try:
        engine.stop()
    except:
        pass

# --------------------------------------------------------------------

def takecommand():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print('listening....')
        eel.DisplayMessage('listening....')
        r.pause_threshold = 1
        r.adjust_for_ambient_noise(source, duration=1)
        audio = r.listen(source, 10, 6)

    try:
        print('recognizing')
        eel.DisplayMessage('recognizing....')
        query = r.recognize_google(audio, language='en-in')
        print(f"user said: {query}")
        eel.DisplayMessage(query)
        return query.lower()
    except Exception:
        return ""

@eel.expose
def allCommands(message=1):
    if message == 1:
        query = takecommand()
    else:
        query = message
        
    if not query:
        return

    eel.senderText(query)
        
    try:
        if "open" in query:
            from engine.features import openCommand
            openCommand(query)
            
        elif "on youtube" in query:
            from engine.features import PlayYoutube
            PlayYoutube(query)
            
        elif any(x in query for x in ["send message", "phone call", "video call"]):
            from engine.features import findContact, whatsApp, makeCall, sendMessage
            contact_no, name = findContact(query)
            if contact_no != 0:
                speak("Which mode you want to use whatsapp or mobile")
                preferance = takecommand()
                if "mobile" in preferance:
                    if "send message" in query or "send sms" in query: 
                        speak("what message to send")
                        msg = takecommand()
                        sendMessage(msg, contact_no, name)
                    elif "phone call" in query:
                        makeCall(name, contact_no)
                elif "whatsapp" in preferance:
                    mode = 'message' if "send message" in query else 'call' if "phone call" in query else 'video call'
                    if mode == 'message':
                        speak("what message to send")
                        query = takecommand()
                    whatsApp(contact_no, query, mode, name)
                    
        # --- NEW: Ash's Learning Engine Trigger ---
        elif "remember that" in query or "remember" in query:
            from engine.features import rememberFact
            rememberFact(query)
            
        else:
            from engine.features import geminai
            geminai(query)
            
    except Exception as e:
        print(f"Error in allCommands logic: {e}")
    
    eel.ShowHood()

# --- THE FINAL BACKGROUND WATCHER BRIDGE ---
hotword_event = None 

def trigger_listening_sequence():
    """Brings app to front and triggers listening"""
    try:
        # 1. Interrupt Current Speech
        stop_speaking()
        
        # 2. FORCE WINDOW TO FRONT
        # This ensures the microphone has priority access
        try:
            app_windows = gw.getWindowsWithTitle("Ash")
            if app_windows:
                win = app_windows[0]
                if win.isMinimized:
                    win.restore()
                win.activate()
                time.sleep(0.3) 
        except Exception as e:
            print(f"Focus Error: {e}")

        # 3. Trigger UI (Siri Animation)
        import pyautogui as autogui
        autogui.hotkey('win', 'j') 
        print("[WATCHER] Siri UI Triggered...")

        # 4. Play chime
        def play_chime():
            try:
                from playsound import playsound
                playsound("www\\assets\\audio\\start_sound.mp3")
            except:
                pass
        threading.Thread(target=play_chime, daemon=True).start()

        # 5. Start Listening
        print("[WATCHER] Mic Opening...")
        eel.spawn(allCommands, 1) 
            
    except Exception as e:
        print(f"Watcher Sequence Error: {e}")

def watch_hotword():
    global hotword_event
    while True:
        if hotword_event and hotword_event.is_set():
            hotword_event.clear() 
            print("\n[WATCHER] Hotword Detected!")
            threading.Thread(target=trigger_listening_sequence, daemon=True).start()
            
        time.sleep(0.1)

threading.Thread(target=watch_hotword, daemon=True).start()