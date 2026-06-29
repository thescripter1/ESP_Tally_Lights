import json
from multiprocessing import Manager
from pathlib import Path



BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config" / "config.json"

def load_state():
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
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
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
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
