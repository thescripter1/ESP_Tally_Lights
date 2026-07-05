import json
import time
import random
from shared_state import get_Mode, set_Kamera
from tally import makeDark, randomize_test_devices, update_tally_states
from settings import CONFIG_FILE, SETTINGS
import PyATEMMax


DEVELOPMENT_MODES = {"development", "develop", "dev", "ccu", "ccu_debug"}


def _get_atem_mode():
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            configured_mode = str(json.load(file).get("Mode", "")).strip().lower()
        if configured_mode in DEVELOPMENT_MODES:
            return "development"
    except (OSError, json.JSONDecodeError):
        pass

    return get_Mode()


def _sleep_while_mode(mode, seconds):
    end_time = time.time() + seconds
    while time.time() < end_time:
        if _get_atem_mode() != mode:
            return False
        time.sleep(min(0.2, end_time - time.time()))
    return True


def _run_test_mode():
    last_src = 0
    last_device_shuffle = 0
    max_camera = SETTINGS["camera_count"]
    current_input = random.randint(1, max_camera)

    while _get_atem_mode() == "test":
        now = time.time()
        if now - last_device_shuffle > 10:
            randomize_test_devices()
            last_device_shuffle = now

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

    while _get_atem_mode() == "production":
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

            while _get_atem_mode() == "production":
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
            if _get_atem_mode() == "production":
                print(f"ATEM reconnect in {reconnect_delay} Sekunden.")
                _sleep_while_mode("production", reconnect_delay)


CCU_DOMAINS = {
    0: "lens",
    1: "camera",
    4: "colorbars",
    8: "chip",
}

CCU_FEATURES = {
    0: {
        0: "focus",
        3: "iris",
        8: "zoom_normalized",
        9: "zoom_speed",
    },
    1: {
        1: "gain",
        2: "white_balance",
        5: "shutter",
        8: "detail",
    },
    4: {
        4: "colorbars",
    },
    8: {
        0: "lift",
        1: "gamma",
        2: "gain",
        4: "contrast",
        5: "lum_mix",
        6: "hue_saturation",
    },
}


def _read_ccu_values(switcher, payload_length):
    values = []
    for offset in range(16, payload_length - 1, 2):
        values.append(switcher._inBuf.getS16(offset))
    return values


def _format_ccu_command(switcher):
    payload_length = switcher._cmdLength - switcher.atem.cmdHeaderLen
    payload = [switcher._inBuf[index] for index in range(payload_length)]

    if payload_length < 3:
        raw_hex = " ".join(f"{byte:02x}" for byte in payload)
        return f"CCU Command: cmd=CCdP payload_too_short={payload_length} raw={raw_hex}"

    camera = switcher._inBuf.getU8(0)
    domain = switcher._inBuf.getU8(1)
    feature = switcher._inBuf.getU8(2)
    domain_name = CCU_DOMAINS.get(domain, "unknown")
    feature_name = CCU_FEATURES.get(domain, {}).get(feature, "unknown")
    values = _read_ccu_values(switcher, payload_length)
    raw_hex = " ".join(f"{byte:02x}" for byte in payload)

    return (
        "CCU Command: "
        f"cmd=CCdP camera={camera} "
        f"domain={domain}({domain_name}) "
        f"feature={feature}({feature_name}) "
        f"values={values} raw={raw_hex}"
    )


def _install_ccu_print_handler(switcher):
    original_handler = switcher._cmdHandlers.get("CCdP", {}).get("callback")

    def print_ccu_command(cmd_str):
        switcher._read2InBuf()
        print(_format_ccu_command(switcher), flush=True)
        if original_handler:
            original_handler(cmd_str)

    switcher._cmdHandlers["CCdP"] = {"callback": print_ccu_command}


def _run_development_mode():
    reconnect_delay = 3

    while _get_atem_mode() == "development":
        switcher = PyATEMMax.ATEMMax()
        try:
            _install_ccu_print_handler(switcher)
            print(f"Versuche Verbindung mit ATEM {SETTINGS['atem_ip']} im Development-Modus")
            switcher.connect(SETTINGS["atem_ip"], connTimeout=3)
            if not switcher.waitForConnection(infinite=False):
                raise TimeoutError("ATEM Verbindung konnte nicht innerhalb des Timeouts hergestellt werden")
            print("ATEM Verbindung hergestellt, CCU Commands werden ausgegeben")

            while _get_atem_mode() == "development":
                time.sleep(0.05)
        except Exception as error:
            print(f"ATEM Development-Verbindung verloren oder fehlgeschlagen: {error}")
        finally:
            try:
                switcher.disconnect()
            except Exception:
                pass
            if _get_atem_mode() == "development":
                print(f"ATEM Development reconnect in {reconnect_delay} Sekunden.")
                _sleep_while_mode("development", reconnect_delay)


def run():
    last_mode = None
    while True:
        mode = _get_atem_mode()
        if mode != last_mode:
            print(f"ATEM Betriebsmodus: {mode}")
            last_mode = mode

        if mode == "test":
            _run_test_mode()
        elif mode == "production":
            _run_production_mode()
        elif mode == "development":
            _run_development_mode()
        else:
            time.sleep(1)
