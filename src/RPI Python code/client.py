from flask import Flask
from flask_socketio import SocketIO
import threading
import time
from shared_state import get_Kamera, get_Liste

app = Flask(__name__, static_folder="static")
socketio = SocketIO(app, cors_allowed_origins="*")

lastKamera = None
lastListe = None


def _register_routes():
    @app.route("/")
    def index():
        return app.send_static_file("client.html")


def _watcher():
    global lastKamera, lastListe

    while True:
        Kamera = get_Kamera()
        Liste = get_Liste()

        if Kamera != lastKamera or Liste != lastListe:
            socketio.emit("Update", {"Kamera": Kamera, "Liste": Liste})
            lastKamera = Kamera
            lastListe = Liste

        time.sleep(0.2)


def run():
    _register_routes()
    threading.Thread(target=_watcher, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=1234)