import time
import paho.mqtt.client as mqtt
from shared_state import get_Liste, set_Pool
from settings import SETTINGS


broker = SETTINGS["mqtt_host"]
client = mqtt.Client()

connected_devices = set()
last_light_colors = {}

def on_message(client, userdata, msg):
    device_id = msg.payload.decode() 
    connected_devices.add(device_id)
    set_Pool(list(connected_devices))

client.on_message = on_message
client.connect(broker, SETTINGS["mqtt_port"], 60)
client.subscribe("tally/lights/status")
client.loop_start()


def calculateBuchstabe(kamernummer):
    tally_liste = get_Liste()
    cameras = tally_liste.get("cameras", [])
    if kamernummer != 0 and kamernummer < len(cameras):
        camera = cameras[kamernummer]
        if isinstance(camera, dict):
            return camera.get("tally")


def _is_assigned_tally(char):
    return char is not None and str(char).strip() not in {"", "0"}


def _publish_light(char, code, force=False):
    if not _is_assigned_tally(char):
        return

    address = f"tally/lights/{char}"
    if not force and last_light_colors.get(address) == code:
        return

    client.publish(address, code)
    last_light_colors[address] = code
    print("Sende Code", code, "an", address)


def make_light(Kameranummer, code, force=False):
    char = calculateBuchstabe(Kameranummer)
    _publish_light(char, code, force=force)


def makeDark(Kameranummer):
    make_light(Kameranummer, SETTINGS["off_color"])

def makeRed(Kameranummer):
    make_light(Kameranummer, SETTINGS["program_color"])


def update_tally_states(program_camera, preview_camera=0):
    tally_liste = get_Liste()
    cameras = tally_liste.get("cameras", [])
    target_colors = {}

    for camera_number, camera in enumerate(cameras):
        if camera_number == 0 or not isinstance(camera, dict):
            continue

        char = camera.get("tally")
        if not _is_assigned_tally(char):
            continue

        color = SETTINGS["off_color"]
        if camera_number == preview_camera:
            color = SETTINGS["preview_color"]
        if camera_number == program_camera:
            color = SETTINGS["program_color"]

        address = f"tally/lights/{char}"
        current_priority = target_colors.get(address, (None, -1))[1]
        priority = 2 if camera_number == program_camera else 1 if camera_number == preview_camera else 0
        if priority >= current_priority:
            target_colors[address] = (color, priority)

    for address, (color, _) in target_colors.items():
        char = address.rsplit("/", 1)[-1]
        _publish_light(char, color)


def makeLila(char):
    print("Folgendes Licht leuchtet nun für 2 Sekunden Lila:", char)
    adress = f"tally/lights/{char}"
    _publish_light(char, SETTINGS["identify_color"], force=True)
    time.sleep(2)
    client.publish(adress, SETTINGS["off_color"])
    last_light_colors[adress] = SETTINGS["off_color"]

def make_Farbe(char, farbe):
    _publish_light(char, farbe, force=True)

def disconnect_Tally():
    client.disconnect()
    
