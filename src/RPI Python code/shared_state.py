import json
from multiprocessing import Manager
import os

CONFIG_FILE = "tally/newLaxoutV1/config/config.json"

def load_state():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                # Optional: prüfen, ob alle Keys vorhanden sind
                if not all(k in data for k in ["Kamera", "Liste", "TallyPool"]):
                    raise ValueError("Ungültige Konfiguration, benutze Standardwerte")
                return data
        except (json.JSONDecodeError, ValueError):
            print("Warnung: config.json ist leer oder beschädigt. Lade Standardwerte.")
    # Standardwerte, falls Datei nicht existiert oder fehlerhaft ist
    return {
        "Kamera": 0,
        "Liste": {
            'cameras': [
                None,
                {'name': 'Kamera 1', 'tally': '0'},
                {'name': 'Kamera 2', 'tally': '0'},
                {'name': 'Kamera 3', 'tally': '0'},
                {'name': 'Kamera 4', 'tally': '0'},
                {'name': 'Kamera 5', 'tally': '0'},
                {'name': 'Kamera 6', 'tally': '0'},
                {'name': 'Kamera 7', 'tally': '0'},
                {'name': 'Kamera 8', 'tally': '0'}
            ]
        },
        "TallyPool": []
    }

# Funktion, um den state in JSON zu speichern
def save_state(state_dict):
    with open(CONFIG_FILE, "w") as f:
        json.dump(state_dict, f, indent=4)

# Manager-Dict erstellen
manager = Manager()
state = manager.dict(load_state())


# Setter- und Getter-Funktionen
def set_Kamera(kamera):
    state["Kamera"] = kamera
    save_state(dict(state))  # nach jeder Änderung speichern
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