import time
import random
from shared_state import set_Kamera
from tally import makeRed, makeDark, disconnect_Tally
import PyATEMMax

current_input = random.randint(1, 8)

def run():
    last_src = 0
    while True:
        # Veränderung erst nach 10–20 Sekunden
        wait_time = random.randint(2, 5)
        time.sleep(wait_time)

        # Neuen Input wählen (aber nicht gleichen wie vorher)
        new_input = current_input
        while new_input == current_input:
            new_input = random.randint(1, 8)

        set_Kamera(new_input)

        src = new_input

        if src != last_src:
            # Alten Port ausschalten, wenn gültig
            if last_src < 9:
                makeDark(last_src)

            # Neuen Port aktivieren, wenn gültig
            if src < 9:
                makeRed(src)
            else:
                print(f"Achtung: src={src} außerhalb von devicelist-Länge (9)). Ignoriere Aktivierung.")

            last_src = src


"""
class ReadAtem:
    def __init__():
        #ATEM Switcher Konfigurieren
        switcher = PyATEMMax.ATEMMax()
        switcher.connect("192.168.2.10")
        switcher.waitForConnection()"""

def run2():
    try:
        print("Versuche verbindung mit ATEM")
        #ATEM Switcher Konfigurieren
        switcher = PyATEMMax.ATEMMax()
        switcher.connect("192.168.2.10")
        switcher.waitForConnection()
        print("ATEM verbindung hergestellt")
    except Exception as e:
        print("Fehler:", e)
    finally:
        try:
            last_src = switcher.programInput[0].videoSource.value
            while True:
                src = switcher.programInput[0].videoSource.value
                if src != last_src:
                    # Alten Port ausschalten, wenn gültig
                    if last_src < 9:
                        makeDark(last_src)
                    # Neuen Port aktivieren, wenn gültig
                    if src < 9:
                        makeRed(src)
                        set_Kamera(src)
                    else:
                        print(f"Achtung: src={src} außerhalb von devicelist-Länge (9). Ignoriere Aktivierung.")

                    last_src = src

                time.sleep(0.01)
        finally:
            disconnect_Tally()
            print("Verbindung getrennt.")