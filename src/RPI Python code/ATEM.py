import time
import random
from shared_state import set_Kamera
from tally import makeRed, makeDark, disconnect_Tally, update_tally_states
from settings import SETTINGS
import PyATEMMax

current_input = random.randint(1, 8)

def run():
    last_src = 0
    max_camera = SETTINGS["camera_count"]
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
            if last_src <= max_camera:
                makeDark(last_src)

            # Neuen Port aktivieren, wenn gültig
            if src <= max_camera:
                update_tally_states(src)
            else:
                print(f"Achtung: src={src} außerhalb der konfigurierten Kameras ({max_camera}). Ignoriere Aktivierung.")

            last_src = src


"""
class ReadAtem:
    def __init__():
        #ATEM Switcher Konfigurieren
        switcher = PyATEMMax.ATEMMax()
        switcher.connect(SETTINGS["atem_ip"])
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
            max_camera = SETTINGS["camera_count"]
            last_program = switcher.programInput[0].videoSource.value
            last_preview = switcher.previewInput[0].videoSource.value
            set_Kamera(last_program)
            update_tally_states(last_program, last_preview)

            while True:
                program_src = switcher.programInput[0].videoSource.value
                preview_src = switcher.previewInput[0].videoSource.value
                if program_src != last_program or preview_src != last_preview:
                    if program_src <= max_camera:
                        update_tally_states(program_src, preview_src)
                        set_Kamera(program_src)
                    else:
                        print(f"Achtung: src={program_src} außerhalb der konfigurierten Kameras ({max_camera}). Ignoriere Aktivierung.")

                    last_program = program_src
                    last_preview = preview_src

                time.sleep(0.01)
        finally:
            disconnect_Tally()
            print("Verbindung getrennt.")
