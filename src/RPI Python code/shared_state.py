import json
import copy
import threading

from settings import CONFIG_FILE, SETTINGS

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
        "Settings": SETTINGS,
    }


def load_state():
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if not all(key in data for key in ["Kamera", "Liste", "TallyPool"]):
                raise ValueError("Pflichtfelder Kamera, Liste oder TallyPool fehlen")
            data["Mode"] = _validated_mode(data.get("Mode", SETTINGS["operating_mode"]))
            data["Settings"] = SETTINGS
            return data
        except json.JSONDecodeError as error:
            print(f"Warnung: config.json ist ungültig. Lade Standardwerte. Fehler: {error}")
        except (OSError, ValueError) as error:
            print(f"Warnung: config.json konnte nicht geladen werden. Lade Standardwerte. Fehler: {error}")

    return default_state()


def save_state(state_dict):
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        state_dict["Settings"] = SETTINGS
        with CONFIG_FILE.open("w", encoding="utf-8") as file:
            json.dump(state_dict, file, indent=4)
    except OSError as error:
        print(f"Warnung: config.json konnte nicht gespeichert werden: {error}")


_state_lock = threading.RLock()
state = load_state()


def set_Kamera(kamera):
    with _state_lock:
        state["Kamera"] = kamera
        save_state(copy.deepcopy(state))
    print("Kamera geändert auf:", kamera)


def get_Kamera():
    with _state_lock:
        return state["Kamera"]


def set_Liste(lst):
    with _state_lock:
        state["Liste"] = lst
        save_state(copy.deepcopy(state))
    print("Liste geändert auf:", lst)


def get_Liste():
    with _state_lock:
        return copy.deepcopy(state["Liste"])


def set_Pool(pool):
    with _state_lock:
        state["TallyPool"] = pool
        save_state(copy.deepcopy(state))
    print("TallyPool geändert auf:", pool)


def get_Pool():
    return state["TallyPool"]


def set_Mode(mode):
    state["Mode"] = _validated_mode(mode)
    save_state(dict(state))
    print("Modus geändert auf:", state["Mode"])


def get_Mode():
    return _validated_mode(state.get("Mode", SETTINGS["operating_mode"]))


print("Liste:   ", get_Liste())
