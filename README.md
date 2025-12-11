# ESP_Tally_Lights
A DIY Tally Light Project for Blackmagic ATEM Video Switchers, wich uses MQTT and an ESP 8266

# Architecture

If you want to build your own Version, you can 3D Print most of the parts. A rough part list can be found under CAD / Part-List

## Setup of Raspberry Pi:
This Repo runs perfectly fine on a Raspberry Pi 3B with the Lite Os. I haven't tested the Desktop Version, but feel free to do so and let me know about your results.
Please note when you install the Lite OS Desktop version with the Raspberry Pi Imager Software, to not configure a WiFi setup. This will give you errors along the way.

### 1. Update the System with:
Connect with the Raspberry Pi Command prompt, idealy via ssh. Because you hopefully have not configured the Wifi, you have to plug in the Pi with an Ethernet Cable

```bash
sudo apt upgrade
sudo apt upgrade -y
```

### 2. Install all the needed dependencies
System Packages:
```bash
sudo apt install -y hostapd dnsmasq
sudo apt install dhcpcd5
sudo apt install python3-pip git -y
```
Python Packages:
```bash
sudo apt install python3-pyatem python3-paho-mqtt
sudo apt install mosquitto mosquitto-clients -y
```

### 3. Configure the Wifi Acess Point from hostapd

```bash
sudo nano /etc/hostapd/hostapd.conf
```

insert the following:
```bash
interface=wlan0
driver=nl80211
ssid=MeinPiNetzwerk
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=MeinSicheresPasswort
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
```






