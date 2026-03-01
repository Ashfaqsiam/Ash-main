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
        # 1. Instantly hide the loader and jump to the Face Auth UI
        eel.hideLoader()
        speak("Ready for Face Authentication")
        
        # 2. Start the camera scan
        flag, name = recoganize.AuthenticateFace()
        
        if flag == 1:
            eel.hideFaceAuth()
            speak("Face Authentication Successful")
            eel.hideFaceAuthSuccess()
            
            speak(f"Hello, Welcome {name} Sir, How can I help you")
            
            eel.hideStart()
            playAssistantSound()
            
            # 3. Run the batch file silently
            subprocess.Popen([r'device.bat']) 
            
        else:
            speak("Face Authentication Failed. Access denied.")
            
    os.system('start msedge.exe --app="http://localhost:8000/index.html"')
    eel.start('index.html', mode=None, host='localhost', block=True)