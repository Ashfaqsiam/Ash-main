import os
import eel
import subprocess

from engine.features import *
from engine.command import *
from engine.auth import recoganize

def start():
    
    eel.init("www")
    playAssistantSound()
    
    # --- NEW: We separate the trigger from the heavy process ---
    @eel.expose
    def init():
        # eel.spawn puts this in the background so the UI updates instantly!
        eel.spawn(run_face_auth) 
        
    def run_face_auth():
        print("[DEBUG] 1. Starting Face Auth Process...")
        
        # This function exists in your UI!
        eel.hideLoader() 
        
        # Give it a moment to clear the screen
        eel.sleep(1.0) 
        
        speak("Ready for Face Authentication")
        
        # 2. Start the camera scan
        # We don't call showFaceAuth anymore because it was causing the crash
        try:
            flag, name = recoganize.AuthenticateFace()
        except Exception as e:
            print(f"[ERROR] Camera failed: {e}")
            flag = 0
        
        if flag == 1:
            # These functions exist in your template!
            eel.hideFaceAuth()
            speak("Face Authentication Successful")
            
            eel.sleep(1.5) 
            eel.hideFaceAuthSuccess()
            
            speak(f"Hello, Welcome {name} Sir. How can I help you?")
            
            eel.hideStart()
            playAssistantSound()
            
            subprocess.Popen([r'device.bat'], shell=True) 
        else:
            speak("Face Authentication Failed.")
            
    os.system('start msedge.exe --app="http://localhost:8000/index.html"')
    eel.start('index.html', mode=None, host='localhost', block=True)