import threading
import client as ClientDashboard
import admin as AdminDashboard
import ATEM as atem

if __name__ == "__main__":
    threads = [
        threading.Thread(target=AdminDashboard.run),
        threading.Thread(target=ClientDashboard.run),
        threading.Thread(target=atem.run)
    ]

    for t in threads:
        t.daemon = True
        t.start()

    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("Beende Programm...")