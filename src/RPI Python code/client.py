from flask import Flask
from flask_socketio import SocketIO
import threading
import time
from shared_state import get_Kamera, get_Liste

app = Flask(__name__, static_folder="static")
socketio = SocketIO(app, cors_allowed_origins="*")

lastKamera = None
lastListe = None
last_message = None

from chat import save_message, get_latest_message

def _register_routes():
    @app.route("/")
    def index():
        return app.send_static_file("client.html")
    
    @socketio.on("chat")
    def handle_mesaage(nachricht):
        #print(nachricht)
        save_message(nachricht)


def _watcher():
    global lastKamera, lastListe, last_message

    while True:
        Kamera = get_Kamera()
        Liste = get_Liste()
        message = get_latest_message()

        if Kamera != lastKamera or Liste != lastListe:
            socketio.emit("Update", {"Kamera": Kamera, "Liste": Liste})
            lastKamera = Kamera
            lastListe = Liste

        if  message != last_message:
            socketio.emit("chat", message)
            last_message = message

        time.sleep(0.2)


def run():
    _register_routes()
    threading.Thread(target=_watcher, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=1234)