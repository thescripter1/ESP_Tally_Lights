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


def make_light(number, state):
    char = calculateBuchstabe(number)
    if char != "0":
        adress = f"tally/lights/{char}"
        client.publish(adress, state)
        print("Sende Nachricht", state, "an", adress)


def makeDark(number):
    make_light(number, 0)

def makeRed(number):
    make_light(number, 1)


def makeLila(char):
    print("Folgendes Licht leuchtet nun für 2 Sekunden Lila:", char)
    adress = f"tally/lights/{char}"
    client.publish(adress, 5)
    time.sleep(2)
    client.publish(adress, 0)

def disconnect_Tally():
    client.disconnect()
    