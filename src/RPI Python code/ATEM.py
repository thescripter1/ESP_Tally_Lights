import time
import random
from shared_state import set_Kamera
from tally import makeDark, update_tally_states
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
    reconnect_delay = 3

    while True:
        switcher = PyATEMMax.ATEMMax()
        try:
            print(f"Versuche Verbindung mit ATEM {SETTINGS['atem_ip']}")
            switcher.connect(SETTINGS["atem_ip"])
            switcher.waitForConnection()
            print("ATEM Verbindung hergestellt")

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

                time.sleep(0.05)
        except Exception as error:
            print(f"ATEM Verbindung verloren oder fehlgeschlagen: {error}")
        finally:
            try:
                switcher.disconnect()
            except Exception:
                pass
            print(f"ATEM reconnect in {reconnect_delay} Sekunden.")
            time.sleep(reconnect_delay)
            


def run3():
    print("In der aktuellen Konfiguration wird nur die ATEM CCU Control Funktionen getestet. Die Tally Lights sind daher nicht aktiv.")
    
    switcher = PyATEMMax.ATEMMax()

    def on_receive(params):
        print(
            "Command:",
            params.get("cmd"),
            "Name:",
            params.get("cmdName")
        )

    switcher.registerEvent(
        switcher.atem.events.receive,
        on_receive
    )

    switcher.connect(SETTINGS["atem_ip"])
    switcher.waitForConnection()

    print("Jetzt am ATEM GAIN, FOCUS, BLACK oder SHUT drücken")
    print("und anschließend die Pfeiltasten betätigen.")

    input("Enter zum Beenden\n")

    switcher.disconnect()
