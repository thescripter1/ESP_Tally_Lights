import time
import paho.mqtt.client as mqtt
from shared_state import get_Liste, set_Pool


broker = "127.0.0.1"
client = mqtt.Client()

connected_devices = set()

def on_message(client, userdata, msg):
    device_id = msg.payload.decode() 
    connected_devices.add(device_id)
    set_Pool(list(connected_devices))

client.on_message = on_message
client.connect(broker, 1883, 60)
client.subscribe("tally/lights/status")
client.loop_start()


def calculateBuchstabe(kamernummer):
    TallyListe = get_Liste()
    if kamernummer != 0:
        return TallyListe["cameras"][kamernummer]["tally"]

def make_light(Kameranummer, code):
    char = calculateBuchstabe(Kameranummer)
    if char != "0" or None:
        adress = f"tally/lights/{char}"
        client.publish(adress, code)
        client.publish(adress, code)
        print("Sende Code", code, "an", adress)


def makeDark(Kameranummer):
    make_light(Kameranummer, "#000000")

def makeRed(Kameranummer):
    make_light(Kameranummer, "#ff0000")


def makeLila(char):
    print("Folgendes Licht leuchtet nun für 2 Sekunden Lila:", char)
    adress = f"tally/lights/{char}"
    client.publish(adress, "#c832c8")
    client.publish(adress, "#c832c8")
    time.sleep(2)
    client.publish(adress, "#000000")
    client.publish(adress, "#000000")

def make_Farbe(char, farbe):
    adress = f"tally/lights/{char}"
    client.publish(adress, farbe)
    client.publish(adress, farbe)

def disconnect_Tally():
    client.disconnect()
    