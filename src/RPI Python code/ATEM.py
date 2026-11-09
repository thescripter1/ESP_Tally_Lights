import time
import random
from shared_state import get_Kamera, get_Mode, set_Kamera
from tally import randomize_test_devices, update_tally_states
from settings import SETTINGS
import PyATEMMax


def _run_test_mode():
    next_camera_change = 0
    next_device_shuffle = 0
    max_camera = SETTINGS["camera_count"]
    current_input = 0

    while get_Mode() == "test":
        now = time.monotonic()
        if now >= next_device_shuffle:
            randomize_test_devices()
            next_device_shuffle = now + 10
        if now >= next_camera_change:
            new_input = random.randint(1, max_camera)
            if max_camera > 1:
                while new_input == current_input:
                    new_input = random.randint(1, max_camera)
            current_input = new_input
            set_Kamera(current_input)
            next_camera_change = now + random.randint(2, 5)
        update_tally_states(current_input)
        time.sleep(0.1)


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

            last_program = None
            while get_Mode() == "production":
                if not switcher.connected:
                    raise ConnectionError("ATEM antwortet nicht mehr")
                program = switcher.programInput[0].videoSource.value
                preview = switcher.previewInput[0].videoSource.value
                if program != last_program:
                    set_Kamera(program)
                    last_program = program
                update_tally_states(program, preview)
                time.sleep(0.1)
        except Exception as error:
            print(f"ATEM Verbindung verloren oder fehlgeschlagen: {error}")
        finally:
            try:
                switcher.disconnect()
            except Exception:
                pass
            if get_Mode() == "production":
                if get_Kamera() != 0:
                    set_Kamera(0)
                retry_at = time.monotonic() + reconnect_delay
                print(f"ATEM reconnect in {reconnect_delay} Sekunden.")
                while get_Mode() == "production" and time.monotonic() < retry_at:
                    update_tally_states(0)
                    time.sleep(0.1)


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
