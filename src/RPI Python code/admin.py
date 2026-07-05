from flask import Flask
from flask_socketio import SocketIO, emit
from pathlib import Path
import threading
import time

from shared_state import get_Kamera, set_Liste, get_Liste, get_Pool, set_Pool
from tally import makeLila, get_device_statuses
from settings import SETTINGS

from chat import save_message, get_latest_message

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__, static_folder=str(BASE_DIR / "static"))
socketio = SocketIO(app, cors_allowed_origins="*")

lastKamera = None
lastListe = None
lastPool = None
lastDevices = None
last_message = None


def _state_payload():
    Pool = get_Pool()
    return {
        "Kamera": get_Kamera(),
        "Liste": get_Liste(),
        "TallyPool": Pool,
        "Pool": Pool,
    }


def _register_routes():
    @app.route("/")
    def index():
        return app.send_static_file("admin.html")

    @socketio.on("connect")
    def handle_connect():
        socketio.emit("Update", _state_payload())

    @socketio.on("admin_command")
    def handle_admin(Liste):
        try:
            if not isinstance(Liste, dict) or not isinstance(Liste.get("cameras"), list):
                raise ValueError("Liste muss ein Objekt mit cameras-Array sein")
            set_Liste(Liste)
            emit("save_status", {"ok": True, "message": "Gespeichert"})
        except Exception as error:
            emit("save_status", {"ok": False, "message": str(error)})

    @socketio.on("markLight")
    def handle_marking(Licht):
        makeLila(Licht)

    @socketio.on("chat")
    def handle_mesaage(nachricht):
        #print(nachricht)
        save_message(nachricht)


def _watcher():
    global lastKamera, lastListe, lastPool, lastDevices, last_message

    while True:
        Kamera = get_Kamera()
        Liste = get_Liste()
        Pool = get_Pool()
        Devices = get_device_statuses()
        message = get_latest_message()

        if Kamera != lastKamera or Liste != lastListe or Pool != lastPool or Devices != lastDevices:
            socketio.emit(
                "Update",
                {"Kamera": Kamera, "Liste": Liste, "Pool": Pool, "Devices": Devices}
            )
            lastKamera = Kamera
            lastListe = Liste
            lastPool = Pool
            lastDevices = Devices

        if  message != last_message:
            socketio.emit("chat", message)
            last_message = message

        time.sleep(0.2)


def run():
    _register_routes()
    threading.Thread(target=_watcher, daemon=True).start()
    socketio.run(app, host=SETTINGS["admin_host"], port=SETTINGS["admin_port"])
