import pyttsx3
import speech_recognition as sr
import eel
import time
import threading 
import pygetwindow as gw
import keyboard 
import re # <-- NEW: We need this to chop the text into sentences

# --- Global flag and Engine Initialization ---
stop_speaking_flag = False
interrupt_flag = False  
speak_lock = threading.Lock()

engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices') 
engine.setProperty('voice', voices[0].id)
engine.setProperty('rate', 174)

# ==========================================
# --- THE MASTER INTERRUPT (KILL SWITCH) ---
# ==========================================
def kill_audio():
    try:
        engine.stop()
    except:
        pass

def master_interrupt():
    global interrupt_flag, stop_speaking_flag
    interrupt_flag = True  
    stop_speaking_flag = True
    print("\n[Interrupt] Spacebar pressed. Halting system...")
    
    # 1. Update the UI to the hood FIRST
    try:
        eel.ShowHood()
    except:
        pass
        
    # 2. Try to kill audio in the background
    threading.Thread(target=kill_audio, daemon=True).start()

keyboard.add_hotkey('space', master_interrupt)
# ==========================================

def onWord(name, location, length):
    global stop_speaking_flag
    if stop_speaking_flag:
        try:
            engine.stop()
        except:
            pass

engine.connect('started-word', onWord)

# --- THE NEW CHUNKED SPEAK FUNCTION ---
def speak(text):
    global stop_speaking_flag, interrupt_flag
    stop_speaking_flag = False 
    
    with speak_lock:
        try:
            text = str(text)
            
            # Safety check before starting
            if interrupt_flag:
                return
                
            eel.DisplayMessage(text)
            eel.receiverText(text)
            
            # CHUNKING TRICK: Split the paragraph by sentences (. ? ! or new lines)
            # This prevents Windows from locking the audio thread for 30 seconds straight
            chunks = re.split(r'(?<=[.!?\n])\s+', text)
            
            for chunk in chunks:
                if not chunk.strip():
                    continue
                    
                # CHECK THE SPACEBAR FLAG BEFORE EVERY SINGLE SENTENCE!
                if interrupt_flag or stop_speaking_flag:
                    print("Speech halted by spacebar.")
                    break # Instantly breaks the loop and stops talking
                
                if getattr(engine, '_in_loop', False):
                    engine.say(chunk)
                else:
                    engine.say(chunk)
                    engine.runAndWait()
                    
        except Exception as e:
            print(f"Speak Error: {e}")

def stop_speaking():
    global stop_speaking_flag
    stop_speaking_flag = True
    threading.Thread(target=kill_audio, daemon=True).start()

# --------------------------------------------------------------------

def takecommand():
    global interrupt_flag
    interrupt_flag = False  

    r = sr.Recognizer()
    m = sr.Microphone()
    
    print('listening....')
    eel.DisplayMessage('listening....')
    
    with m as source:
        r.pause_threshold = 0.5         
        r.non_speaking_duration = 0.3   
        r.adjust_for_ambient_noise(source, duration=0.5) 
        
    audio_queue = []

    def callback(recognizer, audio):
        audio_queue.append(audio)

    stop_listening = r.listen_in_background(m, callback, phrase_time_limit=8)

    interrupted = False
    
    while len(audio_queue) == 0:
        if interrupt_flag:  
            print("Listening stopped by master interrupt.")
            eel.DisplayMessage('Listening cancelled...')
            interrupted = True
            break
        time.sleep(0.05)
        
    stop_listening(wait_for_stop=True) 

    if interrupted:
        return ""

    audio = audio_queue[0]

    try:
        print('recognizing')
        eel.DisplayMessage('recognizing....')
        query = r.recognize_google(audio, language='en-in')
        
        if interrupt_flag:
            return ""
            
        print(f"user said: {query}")
        eel.DisplayMessage(query)
        return query.lower()
    except Exception:
        return ""

@eel.expose
def allCommands(message=1):
    global interrupt_flag
    
    # --- NEW: CONTINUOUS CONVERSATION LOOP ---
    while True:
        if message == 1:
            query = takecommand()
        else:
            query = message
            message = 1  # Reset to 1 so the NEXT loop iteration listens to the mic automatically!
            
        # If spacebar is pressed or Ash hears nothing, break the loop and go to sleep
        if interrupt_flag or not query:
            eel.ShowHood() 
            break

        eel.senderText(query)
        
        # --- NEW: EXIT COMMANDS ---
        # If you say any of these words, Ash will say goodbye and go to sleep
        exit_words = ["bye", "goodbye", "exit", "stop", "go to sleep", "sleep", "shut down", "turn off"]
        if any(word in query for word in exit_words):
            speak("Goodbye Sir! Let me know if you need anything else.")
            eel.ShowHood()
            break
            
        try:
            if "open" in query:
                from engine.features import openCommand
                openCommand(query)
                
            elif "on youtube" in query:
                from engine.features import PlayYoutube
                PlayYoutube(query)
                
            elif any(x in query for x in ["send message", "phone call", "video call", "make a call", "call", "message"]):
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
                        
            elif "remember that" in query or "remember" in query:
                from engine.features import rememberFact
                rememberFact(query)

            # ==========================================
            # --- NEW: ASH ALARM COMMAND ---
            # ==========================================
            elif "set alarm" in query or "set an alarm" in query:
                speak("For what time, Sir? Please say the hour and minute, like 6:30 AM.")
                
                # Ash will listen immediately for your time input
                alarm_time = takecommand()
                
                if alarm_time != "":
                    from engine.features import set_alarm
                    set_alarm(alarm_time)
                else:
                    speak("I didn't catch the time. Alarm cancelled.")
                
            # ==========================================
            # --- ASH VISION COMMANDS ---
            # ==========================================
            elif any(x in query for x in ["what is this", "look at this", "what am i holding", "what is in front of you", "can you see this"]):
                from engine.features import ash_vision
                ash_vision(query)
                
            else:
                from engine.features import hybrid_ai_brain
                hybrid_ai_brain(query)
                
        except Exception as e:
            print(f"Error in allCommands logic: {e}")
        
        # Check if the spacebar was pressed while Ash was thinking/talking
        if interrupt_flag:
            eel.ShowHood()
            break
        
        # Notice we removed the final eel.ShowHood() here so the loop can keep going!

# --- THE FINAL BACKGROUND WATCHER BRIDGE ---
hotword_event = None 

def trigger_listening_sequence():
    """Brings app to front and triggers listening"""
    try:
        stop_speaking()
        
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

        import pyautogui as autogui
        autogui.hotkey('win', 'j') 
        print("[WATCHER] Siri UI Triggered...")

        def play_chime():
            try:
                from playsound import playsound
                playsound("www\\assets\\audio\\start_sound.mp3")
            except:
                pass
        threading.Thread(target=play_chime, daemon=True).start()

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

@eel.expose
def textCommand(message):
    """Safely handles typed text from the frontend without freezing the UI"""
    global interrupt_flag
    interrupt_flag = False # Reset the kill switch just in case
    
    # eel.spawn pushes the continuous loop into the background!
    eel.spawn(allCommands, message)