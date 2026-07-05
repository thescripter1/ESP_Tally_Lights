import time
import random
from shared_state import get_Mode, set_Kamera
from tally import makeDark, update_tally_states
from settings import SETTINGS
import PyATEMMax


def _sleep_while_mode(mode, seconds):
    end_time = time.time() + seconds
    while time.time() < end_time:
        if get_Mode() != mode:
            return False
        time.sleep(min(0.2, end_time - time.time()))
    return True


def _run_test_mode():
    last_src = 0
    max_camera = SETTINGS["camera_count"]
    current_input = random.randint(1, max_camera)

    while get_Mode() == "test":
        if not _sleep_while_mode("test", random.randint(2, 5)):
            return

        # Neuen Input wählen (aber nicht gleichen wie vorher)
        new_input = current_input
        if max_camera > 1:
            while new_input == current_input:
                new_input = random.randint(1, max_camera)

        set_Kamera(new_input)
        current_input = new_input

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

def _run_production_mode():
    reconnect_delay = 3

    while get_Mode() == "production":
        switcher = PyATEMMax.ATEMMax()
        try:
            print(f"Versuche Verbindung mit ATEM {SETTINGS['atem_ip']}")
            switcher.connect(SETTINGS["atem_ip"], connTimeout=3)
            if not switcher.waitForConnection(infinite=False):
                raise TimeoutError("ATEM Verbindung konnte nicht innerhalb des Timeouts hergestellt werden")
            print("ATEM Verbindung hergestellt")

            max_camera = SETTINGS["camera_count"]
            last_program = switcher.programInput[0].videoSource.value
            last_preview = switcher.previewInput[0].videoSource.value
            set_Kamera(last_program)
            update_tally_states(last_program, last_preview)

            while get_Mode() == "production":
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
            if get_Mode() == "production":
                print(f"ATEM reconnect in {reconnect_delay} Sekunden.")
                _sleep_while_mode("production", reconnect_delay)


def run():
    last_mode = None
    while True:
        mode = get_Mode()
        if mode != last_mode:
            print(f"ATEM Betriebsmodus: {mode}")
            last_mode = mode

        if mode == "test":
            _run_test_mode()
        elif mode == "production":
            _run_production_mode()
        else:
            time.sleep(1)
