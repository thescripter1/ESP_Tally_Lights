import json
import os
import re
from ipaddress import ip_address
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
    "program_color": "#ff0000",
    "preview_color": "#00ff00",
    "off_color": "#000000",
    "identify_color": "#c832c8",
    "operating_mode": "production",
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
    "TALLY_PROGRAM_COLOR": "program_color",
    "TALLY_PREVIEW_COLOR": "preview_color",
    "TALLY_OFF_COLOR": "off_color",
    "TALLY_IDENTIFY_COLOR": "identify_color",
    "TALLY_OPERATING_MODE": "operating_mode",
}

INT_FIELDS = {"mqtt_port", "admin_port", "client_port", "camera_count"}


def _read_config_file():
    if not CONFIG_FILE.exists():
        return {}

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if isinstance(data, dict):
            return data
        print("Warnung: config.json muss ein Objekt sein. Nutze Standardwerte.")
    except OSError as error:
        print(f"Warnung: config.json konnte nicht gelesen werden: {error}")
    except (json.JSONDecodeError, UnicodeError) as error:
        print(f"Warnung: config.json ist ungültig: {error}")

    return {}


def validate_setting(name, value):
    text = str(value).strip()
    if name in INT_FIELDS:
        try:
            number = int(text)
        except ValueError:
            number = 0
        if number > 0 and (not name.endswith("_port") or number <= 65535):
            return number
    elif name.endswith("_color"):
        if re.fullmatch(r"#[0-9a-fA-F]{6}", text):
            return text
    elif name == "operating_mode":
        if text in {"production", "test"}:
            return text
    elif name == "atem_ip" or name.endswith("_host"):
        try:
            address = ip_address(text)
            if name != "atem_ip" or address.version == 4:
                return str(address)
        except ValueError:
            labels = text.removesuffix(".").split(".")
            if len(text) <= 253 and all(
                re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?", label)
                for label in labels
            ) and not all(label.isdigit() for label in labels):
                return text
    raise ValueError(f"Ungültiger Wert für {name}: {value!r}")


def _validated(settings):
    result = DEFAULT_SETTINGS.copy()

    for key, value in settings.items():
        if key not in DEFAULT_SETTINGS:
            print(f"Warnung: Unbekannte Einstellung {key!r} in config.json wird ignoriert.")
            continue

        try:
            result[key] = validate_setting(key, value)
        except ValueError as error:
            print(f"Warnung: {error}. Nutze Standard {result[key]!r}.")

    return result


def load_settings():
    config = _read_config_file()
    settings = config.get("Settings", {})

    if not isinstance(settings, dict):
        print("Warnung: 'Settings' in config.json muss ein Objekt sein. Nutze Standardwerte.")
        settings = {}

    merged = dict(settings)
    for env_name, setting_name in ENV_OVERRIDES.items():
        if env_name in os.environ:
            merged[setting_name] = os.environ[env_name]

    return _validated(merged)


SETTINGS = load_settings()
