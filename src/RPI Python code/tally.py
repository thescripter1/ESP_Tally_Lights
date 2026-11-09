import time
import random
import threading
import paho.mqtt.client as mqtt
from shared_state import get_Liste, get_Mode, set_Pool
from settings import SETTINGS


broker = SETTINGS["mqtt_host"]
client = mqtt.Client()

connected_devices = set()
device_last_seen = {}
test_connected_devices = {}
last_light_colors = {}
_tally_lock = threading.RLock()
_tally_colors = {}
_identifying = {}
DEVICE_TIMEOUT_SECONDS = 30
TEST_DEVICE_IDS = tuple("ABCDEFGHJKLMNPQRSTUVWXYZ")


def on_connect(client, userdata, flags, rc, *args):
    if rc == 0:
        print(f"MQTT verbunden: {broker}:{SETTINGS['mqtt_port']}")
        client.subscribe("tally/lights/status")
    else:
        print(f"MQTT Verbindung fehlgeschlagen, rc={rc}")


def on_disconnect(client, userdata, rc, *args):
    if rc != 0:
        print("MQTT Verbindung verloren. Versuche automatisch erneut zu verbinden.")
    else:
        print("MQTT Verbindung getrennt.")


def on_message(client, userdata, msg):
    device_id = msg.payload.decode().strip()
    if not device_id:
        return
    connected_devices.add(device_id)
    device_last_seen[device_id] = time.time()
    set_Pool(list(connected_devices))


client.on_message = on_message
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.reconnect_delay_set(min_delay=1, max_delay=30)
client.connect_async(broker, SETTINGS["mqtt_port"], 60)
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

    try:
        result = client.publish(address, code)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            last_light_colors[address] = code
            print("Sende Code", code, "an", address)
        else:
            print(f"MQTT Publish an {address} konnte nicht direkt gesendet werden, rc={result.rc}")
    except Exception as error:
        print(f"MQTT Publish an {address} fehlgeschlagen: {error}")


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

    with _tally_lock:
        previous_devices = set(_tally_colors)
        _tally_colors.update({address: color for address, (color, _) in target_colors.items()})
        for address in previous_devices - target_colors.keys():
            _tally_colors[address] = SETTINGS["off_color"]

        for address, color in list(_tally_colors.items()):
            char = address.rsplit("/", 1)[-1]
            if char in _identifying:
                continue
            _publish_light(char, color)
            if address not in target_colors and last_light_colors.get(address) == color:
                del _tally_colors[address]


def makeLila(char):
    if not isinstance(char, str) or not _is_assigned_tally(char):
        return
    deadline = time.monotonic() + 2
    with _tally_lock:
        _identifying[char] = deadline
        _publish_light(char, SETTINGS["identify_color"], force=True)
    time.sleep(2)
    with _tally_lock:
        if _identifying.get(char) == deadline:
            del _identifying[char]
            address = f"tally/lights/{char}"
            _publish_light(char, _tally_colors.get(address, SETTINGS["off_color"]))


def make_Farbe(char, farbe):
    _publish_light(char, farbe, force=True)

def disconnect_Tally():
    client.disconnect()


def get_device_statuses():
    if get_Mode() == "test":
        return _get_test_device_statuses()

    now = time.time()
    statuses = []
    for device_id in sorted(connected_devices):
        last_seen = device_last_seen.get(device_id, 0)
        statuses.append({
            "id": device_id,
            "online": now - last_seen <= DEVICE_TIMEOUT_SECONDS,
            "lastSeen": last_seen,
        })
    return statuses


def randomize_test_devices():
    now = time.time()
    max_devices = min(len(TEST_DEVICE_IDS), max(4, SETTINGS["camera_count"]))
    count = random.randint(2, max_devices)
    selected = random.sample(TEST_DEVICE_IDS, count)

    test_connected_devices.clear()
    for device_id in selected:
        online = random.random() > 0.2
        test_connected_devices[device_id] = {
            "online": online,
            "lastSeen": now if online else now - random.randint(DEVICE_TIMEOUT_SECONDS + 5, DEVICE_TIMEOUT_SECONDS + 90),
        }


def get_visible_pool():
    if get_Mode() == "test":
        if not test_connected_devices:
            randomize_test_devices()
        return sorted(test_connected_devices)
    return list(connected_devices)


def _get_test_device_statuses():
    if not test_connected_devices:
        randomize_test_devices()

    return [
        {
            "id": device_id,
            "online": details["online"],
            "lastSeen": details["lastSeen"],
        }
        for device_id, details in sorted(test_connected_devices.items())
    ]
