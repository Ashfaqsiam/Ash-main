import multiprocessing

# To run Ash
def startAsh(hotword_event, auth_event):
        # Hotword event ta command file e pathiye dicchi
        import engine.command
        engine.command.hotword_event = hotword_event
        
        # Share the auth lock with main.py so we can unlock it later
        import main
        main.auth_event = auth_event
        
        print("Process 1 (Ash UI) is running.")
        main.start()

# To run hotword
def listenHotword(hotword_event, auth_event):
        print("Process 2 (Hotword) is WAITING for Authentication...")
        
        # MAGIC LINE: This completely pauses the microphone until login is successful!
        auth_event.wait() 
        
        print("Authentication Complete! Microphone is now listening.")
        from engine.features import hotword
        # Hotword function ke event ta pass kore dicchi
        hotword(hotword_event)


if __name__ == '__main__':
        # EI SWICTH TA DUITO PROCESS KE CONNECT KORBE
        hotword_event = multiprocessing.Event()
        
        # NEW SWITCH: Controls when the microphone turns on
        auth_event = multiprocessing.Event()
        
        # Args hishebe event ta pass kora hoyeche
        p1 = multiprocessing.Process(target=startAsh, args=(hotword_event, auth_event))
        p2 = multiprocessing.Process(target=listenHotword, args=(hotword_event, auth_event))
        
        p1.start()
        # Removed the redundant device.bat call here since it runs in main.py now!
        p2.start()
        
        p1.join()

        if p2.is_alive():
            p2.terminate()
            p2.join()

        print("system stop")