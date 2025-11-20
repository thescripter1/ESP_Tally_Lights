from flask import Flask
from flask_socketio import SocketIO
import threading
import time
from shared_state import get_Kamera, set_Liste, get_Liste, get_Pool
from tally import makeLila

app = Flask(__name__, static_folder="static")
socketio = SocketIO(app, cors_allowed_origins="*")

lastKamera = None
lastListe = None
lastPool = None


def _register_routes():
    @app.route("/")
    def index():
        return app.send_static_file("admin.html")

    @socketio.on("admin_command")
    def handle_admin(Liste):
        set_Liste(Liste)

    @socketio.on("markLight")
    def handle_marking(Licht):
        makeLila(Licht)


def _watcher():
    global lastKamera, lastListe, lastPool

    while True:
        Kamera = get_Kamera()
        Liste = get_Liste()
        Pool = get_Pool()

        if Kamera != lastKamera or Liste != lastListe or Pool != lastPool:
            socketio.emit(
                "Update",
                {"Kamera": Kamera, "Liste": Liste, "Pool": Pool}
            )
            lastKamera = Kamera
            lastListe = Liste
            lastPool = Pool

        time.sleep(0.2)


def run():
    _register_routes()
    threading.Thread(target=_watcher, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=4321)