import json
import copy
import os
import tempfile
import threading

from settings import CONFIG_FILE, DEFAULT_SETTINGS, SETTINGS, validate_setting

MODE_VALUES = {"production", "test"}


def _validated_mode(mode):
    normalized = str(mode or "").strip().lower()
    if normalized in MODE_VALUES:
        return normalized
    print(f"Warnung: Ungültiger Modus {mode!r}. Nutze production.")
    return "production"


def _default_cameras():
    cameras = [None]
    for index in range(1, SETTINGS["camera_count"] + 1):
        cameras.append({"name": f"Kamera {index}", "tally": "0"})
    return cameras


def default_state():
    return {
        "Kamera": 0,
        "Liste": {
            "cameras": _default_cameras()
        },
        "TallyPool": [],
        "Mode": _validated_mode(SETTINGS["operating_mode"]),
        "Settings": {},
    }


def load_state():
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if not isinstance(data, dict):
                raise ValueError("config.json muss ein Objekt sein")
            data = {**default_state(), **data}
            if not isinstance(data["Liste"], dict) or not isinstance(data["Liste"].get("cameras"), list):
                data["Liste"] = default_state()["Liste"]
            if not isinstance(data["TallyPool"], list):
                data["TallyPool"] = []
            data["Mode"] = _validated_mode(data.get("Mode", SETTINGS["operating_mode"]))
            if not isinstance(data.get("Settings"), dict):
                data["Settings"] = {}
            return data
        except json.JSONDecodeError as error:
            print(f"Warnung: config.json ist ungültig. Lade Standardwerte. Fehler: {error}")
        except (OSError, ValueError) as error:
            print(f"Warnung: config.json konnte nicht geladen werden. Lade Standardwerte. Fehler: {error}")

    return default_state()


def save_state(state_dict):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=CONFIG_FILE.parent, delete=False
    ) as file:
        temp_path = file.name
        try:
            json.dump(state_dict, file, indent=4)
            file.flush()
            os.replace(temp_path, CONFIG_FILE)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


_state_lock = threading.RLock()
state = load_state()


def _set_state(key, value, require_save=False):
    with _state_lock:
        updated_state = {**state, key: value}
        try:
            save_state(updated_state)
        except OSError as error:
            if require_save:
                raise
            print(f"Warnung: config.json konnte nicht gespeichert werden: {error}")
        state[key] = copy.deepcopy(value)


def set_Kamera(kamera):
    _set_state("Kamera", kamera)


def get_Kamera():
    with _state_lock:
        return state["Kamera"]


def set_Liste(lst):
    _set_state("Liste", lst, require_save=True)


def get_Liste():
    with _state_lock:
        return copy.deepcopy(state["Liste"])


def set_Pool(pool):
    _set_state("TallyPool", pool)


def get_Pool():
    with _state_lock:
        return list(state["TallyPool"])


def set_Mode(mode):
    if mode not in MODE_VALUES:
        raise ValueError("Bitte Produktion oder Test wählen.")
    _set_state("Mode", mode, require_save=True)


def get_Mode():
    with _state_lock:
        return _validated_mode(state.get("Mode", SETTINGS["operating_mode"]))


ADMIN_SETTINGS = ("atem_ip", "mqtt_host", "mqtt_port", "admin_port", "client_port")


def get_server_settings():
    with _state_lock:
        return {
            name: state["Settings"].get(name, DEFAULT_SETTINGS[name])
            for name in ADMIN_SETTINGS
        }


def set_server_settings(values):
    if not isinstance(values, dict) or values.keys() != set(ADMIN_SETTINGS):
        raise ValueError("Die Server-Einstellungen sind unvollständig.")
    validated = {name: validate_setting(name, value) for name, value in values.items()}
    with _state_lock:
        _set_state("Settings", {**state["Settings"], **validated}, require_save=True)
