import os
import eel
import subprocess

from engine.features import *
from engine.command import *
from engine.auth import recoganize

def start():
    eel.init("www")
    
    # ----------------------------------------------------
    # --- 1. INITIALIZATION (Loader -> Auth Hub) ---
    # ----------------------------------------------------
    @eel.expose
    def init():
        # Run the boot sequence in the background so it doesn't freeze the UI
        eel.spawn(boot_up_sequence)
        
    def boot_up_sequence():
        # 1. Play startup sound immediately for the Blue Circle
        playAssistantSound()
        print("[System] Booting up Loader...")
        
        # 2. Let the Blue Circle spin for 2.5 seconds
        eel.sleep(2.5) 
        
        # 3. Tell JS to hide the Loader and show the Login Buttons
        try:
            eel.showAuthScreen()
            speak("System initialized. Please select an authentication method.")
        except Exception as e:
            print(f"UI Transition Error: {e}")

    # ----------------------------------------------------
    # --- 2. FACIAL RECOGNITION PROTOCOL ---
    # ----------------------------------------------------
    @eel.expose
    def start_face_auth():
        # Run in the background so the UI doesn't freeze
        eel.spawn(run_face_auth)
        
    def run_face_auth():
        print("[DEBUG] Starting Face Auth Process...")
        speak("Initializing Facial Recognition Protocol.")
        
        try:
            eel.showFaceAuth() 
        except:
            pass
            
        try:
            flag, name = recoganize.AuthenticateFace()
        except Exception as e:
            print(f"[ERROR] Camera failed: {e}")
            flag = 0
            
        if flag == 1:
            try:
                eel.hideFaceAuth()
            except: pass
            
            speak("Face Authentication Successful.")
            
            try:
                eel.showFaceAuthSuccess()
                eel.sleep(1.5) 
                eel.hideFaceAuthSuccess()
            except:
                pass
                
            speak(f"Welcome {name} Sir.")
            boot_main_system()
        else:
            speak("Face Authentication Failed. Access Denied.")
            # Reset the buttons on the UI so the user can try again
            eel.resetAuthUI("Face Not Recognized") 

    # ----------------------------------------------------
    # --- 3. VOICE RECOGNITION PROTOCOL (Passphrase) ---
    # ----------------------------------------------------
    @eel.expose
    def start_voice_auth():
        eel.spawn(run_voice_auth)
        
    def run_voice_auth():
        print("[DEBUG] Starting Voice Auth...")
        
        # 1. Prompt the user
        speak("Voice Authentication Activated. Please state your secure passphrase.")
        
        # 2. Listen using your existing Speech Recognition function
        eel.sleep(0.5)
        attempt = takecommand().lower()
        print(f"[VOICE AUTH] System Heard: '{attempt}'")
        
        # ==========================================
        # 3. YOUR SECRET PASSWORD
        # Checks for words, raw numbers, and spaced numbers!
        # ==========================================
        if attempt == "":
            speak("I did not catch that. Authentication cancelled.")
            eel.resetAuthUI("No Audio Detected")
            
        elif "five six eight zero nine nine" in attempt or "568099" in attempt or "5 6 8 0 9 9" in attempt:
            speak("Passphrase accepted. Voice match confirmed.")
            boot_main_system()
            
        else:
            speak("Passphrase incorrect. Access Denied.")
            eel.resetAuthUI("Access Denied")

    # ----------------------------------------------------
    # --- 4. GUEST MODE (BYPASS) ---
    # ----------------------------------------------------
    @eel.expose
    def start_guest_mode():
        eel.spawn(run_guest_mode)
        
    def run_guest_mode():
        print("[DEBUG] Bypassing Auth -> Guest Mode")
        speak("Bypassing security protocols. Welcome, Guest.")
        boot_main_system()

    # ----------------------------------------------------
    # --- 5. SYSTEM BOOT SEQUENCE ---
    # ----------------------------------------------------
    def boot_main_system():
        """This runs when ANY authentication is successful"""
        print("[DEBUG] Booting Main UI...")
        
        try:
            eel.hideStart() # Hides the entire login screen
        except:
            pass
            
        playAssistantSound()
        speak("How can I help you?")
        
        # Start your external device script
        try:
            subprocess.Popen([r'device.bat'], shell=True) 
        except Exception as e:
            print(f"Could not run device.bat: {e}")

        # ==========================================
        # --- WAKE UP THE MICROPHONE ---
        # ==========================================
        import main
        if hasattr(main, 'auth_event'):
            main.auth_event.set() # This unlocks auth_event.wait() in run.py!

    # --- START THE APP (Strict No-Cache Mode) ---
    try:
        # First, try to force Google Chrome in Incognito Mode
        eel.start('index.html', mode='chrome', host='localhost', block=True, cmdline_args=['--incognito'])
    except Exception:
        # If Chrome isn't installed, fallback to Edge in Private Mode
        eel.start('index.html', mode='edge', host='localhost', block=True, cmdline_args=['-inprivate'])