import json
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config" / "config.json"

DEFAULT_SETTINGS = {
    "atem_ip": "192.168.2.10",
    "mqtt_host": "127.0.0.1",
    "mqtt_port": 1883,
    "admin_host": "0.0.0.0",
    "admin_port": 4321,
    "client_host": "0.0.0.0",
    "client_port": 1234,
    "camera_count": 8,
}

ENV_OVERRIDES = {
    "TALLY_ATEM_IP": "atem_ip",
    "TALLY_MQTT_HOST": "mqtt_host",
    "TALLY_MQTT_PORT": "mqtt_port",
    "TALLY_ADMIN_HOST": "admin_host",
    "TALLY_ADMIN_PORT": "admin_port",
    "TALLY_CLIENT_HOST": "client_host",
    "TALLY_CLIENT_PORT": "client_port",
    "TALLY_CAMERA_COUNT": "camera_count",
}

INT_FIELDS = {"mqtt_port", "admin_port", "client_port", "camera_count"}


def _read_config_file():
    if not CONFIG_FILE.exists():
        return {}

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except OSError as error:
        print(f"Warnung: config.json konnte nicht gelesen werden: {error}")
    except json.JSONDecodeError as error:
        print(f"Warnung: config.json ist ungültig: {error}")

    return {}


def _coerce_int(name, value, fallback):
    try:
        converted = int(value)
    except (TypeError, ValueError):
        print(f"Warnung: Ungültiger Wert für {name!r}: {value!r}. Nutze Standard {fallback!r}.")
        return fallback

    if converted <= 0:
        print(f"Warnung: {name!r} muss größer als 0 sein. Nutze Standard {fallback!r}.")
        return fallback

    return converted


def _validated(settings):
    result = DEFAULT_SETTINGS.copy()

    for key, value in settings.items():
        if key not in DEFAULT_SETTINGS:
            print(f"Warnung: Unbekannte Einstellung {key!r} in config.json wird ignoriert.")
            continue

        if key in INT_FIELDS:
            result[key] = _coerce_int(key, value, DEFAULT_SETTINGS[key])
        elif value is None or str(value).strip() == "":
            print(f"Warnung: Leerer Wert für {key!r}. Nutze Standard {DEFAULT_SETTINGS[key]!r}.")
        else:
            result[key] = str(value).strip()

    return result


def load_settings():
    config = _read_config_file()
    settings = config.get("Settings", {})

    if settings and not isinstance(settings, dict):
        print("Warnung: 'Settings' in config.json muss ein Objekt sein. Nutze Standardwerte.")
        settings = {}

    merged = dict(settings)
    for env_name, setting_name in ENV_OVERRIDES.items():
        if env_name in os.environ:
            merged[setting_name] = os.environ[env_name]

    return _validated(merged)


SETTINGS = load_settings()

