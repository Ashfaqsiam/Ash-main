import multiprocessing
import subprocess

# To run Ash
def startAsh(hotword_event):
        # Hotword event ta command file e pathiye dicchi
        import engine.command
        engine.command.hotword_event = hotword_event
        
        print("Process 1 (Ash & Camera) is running.")
        from main import start
        start()

# To run hotword
def listenHotword(hotword_event):
        print("Process 2 (Hotword) is running.")
        from engine.features import hotword
        # Hotword function ke event ta pass kore dicchi
        hotword(hotword_event)


if __name__ == '__main__':
        # EI SWICTH TA DUITO PROCESS KE CONNECT KORBE
        hotword_event = multiprocessing.Event()
        
        # Args hishebe event ta pass kora hoyeche
        p1 = multiprocessing.Process(target=startAsh, args=(hotword_event,))
        p2 = multiprocessing.Process(target=listenHotword, args=(hotword_event,))
        
        p1.start()
        p2.start()
        
        p1.join()

        if p2.is_alive():
            p2.terminate()
            p2.join()

        print("system stop")