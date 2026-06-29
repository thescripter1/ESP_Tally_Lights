import json
from multiprocessing import Manager

from settings import CONFIG_FILE, SETTINGS


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
        "Settings": SETTINGS,
    }


def load_state():
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if not all(key in data for key in ["Kamera", "Liste", "TallyPool"]):
                raise ValueError("Pflichtfelder Kamera, Liste oder TallyPool fehlen")
            data["Settings"] = SETTINGS
            return data
        except json.JSONDecodeError as error:
            print(f"Warnung: config.json ist ungültig. Lade Standardwerte. Fehler: {error}")
        except (OSError, ValueError) as error:
            print(f"Warnung: config.json konnte nicht geladen werden. Lade Standardwerte. Fehler: {error}")

    return default_state()


def save_state(state_dict):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    state_dict["Settings"] = SETTINGS
    with CONFIG_FILE.open("w", encoding="utf-8") as file:
        json.dump(state_dict, file, indent=4)


manager = Manager()
state = manager.dict(load_state())


def set_Kamera(kamera):
    state["Kamera"] = kamera
    save_state(dict(state))
    print("Kamera geändert auf:", kamera)


def get_Kamera():
    return state["Kamera"]


def set_Liste(lst):
    state["Liste"] = lst
    save_state(dict(state))
    print("Liste geändert auf:", lst)


def get_Liste():
    return state["Liste"]


def set_Pool(pool):
    state["TallyPool"] = pool
    save_state(dict(state))
    print("TallyPool geändert auf:", pool)


def get_Pool():
    return state["TallyPool"]


print("Liste:   ", get_Liste())

