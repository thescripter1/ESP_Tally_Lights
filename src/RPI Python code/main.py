import threading
import client as ClientDashboard
import admin as AdminDashboard
import ATEM as atem
from settings import SETTINGS

if __name__ == "__main__":
    print("Starte Tally Lights Server")
    print(f"ATEM: {SETTINGS['atem_ip']}")
    print(f"MQTT: {SETTINGS['mqtt_host']}:{SETTINGS['mqtt_port']}")
    print(f"Admin UI: http://{SETTINGS['admin_host']}:{SETTINGS['admin_port']}")
    print(f"Client UI: http://{SETTINGS['client_host']}:{SETTINGS['client_port']}")

    threads = [
        threading.Thread(target=AdminDashboard.run),
        threading.Thread(target=ClientDashboard.run),
        threading.Thread(target=atem.run2)
    ]

    for t in threads:
        t.daemon = True
        t.start()

    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("Beende Programm...")
