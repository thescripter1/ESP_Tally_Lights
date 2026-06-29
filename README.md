# ESP Tally Lights

A DIY wireless tally light system for Blackmagic ATEM video switchers. A Raspberry Pi reads the current program input from the ATEM, publishes tally states over MQTT, and ESP8266-based tally lights subscribe to their assigned MQTT topics.

> [!WARNING]
> [!NOTE]
> Some code and variable names are still German. Runtime network and service settings are configured through `config/config.json` or environment variables.

![ESP Tally Light](https://github.com/user-attachments/assets/def7a56f-405d-4a1b-bcd7-a389e9b9be46)

## What It Does

- Reads the active program input from a Blackmagic ATEM switcher.
- Sends tally commands to ESP8266 tally lights via MQTT.
- Uses a Raspberry Pi as both the tally server and Wi-Fi access point.
- Provides an admin dashboard for assigning physical tally lights to cameras.
- Provides a client dashboard for phones, tablets, or crew members who only need to see the current live camera.
- Supports a small shared chat between admin/client dashboards.

## Architecture

```text
Blackmagic ATEM
192.168.2.10
      |
      | Ethernet
      |
Raspberry Pi
eth0: 192.168.2.11
wlan0: 192.168.4.1
MQTT broker: 1883
Admin UI: 4321
Client UI: 1234
      |
      | Wi-Fi: Tally-Lights
      |
ESP8266 tally lights
MQTT topic: tally/lights/<ID>
```

The Raspberry Pi connects to the ATEM over Ethernet and creates its own Wi-Fi network for the tally lights and dashboard clients. Each ESP8266 has a single character ID, for example `A`, `B`, or `C`, and listens on `tally/lights/<ID>`.

## Repository Layout

```text
src/
  Arduino Code/
    ESP_Tally_Light/
      ESP_Tally_Light.ino       ESP8266 firmware
  RPI Python code/
    main.py                     Starts admin UI, client UI, and ATEM listener
    ATEM.py                     Reads ATEM program input
    tally.py                    Publishes MQTT color commands
    admin.py                    Admin dashboard server, port 4321
    client.py                   Client dashboard server, port 1234
    shared_state.py             Shared camera/tally configuration
    static/                     HTML dashboards
    config/config.json          Example configuration
```

## Hardware

Minimum tested setup:

- Raspberry Pi 3B or similar, preferably with Raspberry Pi OS Lite.
- Blackmagic ATEM switcher reachable over Ethernet.
- ESP8266 board, for example Wemos D1 mini.
- WS2812B/NeoPixel compatible LED strip or LED ring.
- 3D printed tally light housing.
- 5 V power supply suitable for the ESP8266 and LEDs.

The detailed mechanical build, wiring photos, CAD files, print settings, and part list are better suited for a GitHub Wiki page because they are more photo-heavy and likely to change independently from the code. This README focuses on getting the software running.

## Default Network Settings

These values are used by the current code and examples:

| Item | Default |
| --- | --- |
| Pi Wi-Fi SSID | `Tally-Lights` |
| Pi Wi-Fi password | `MeinSicheresPasswort` |
| Pi Wi-Fi IP | `192.168.4.1/24` |
| MQTT broker | `192.168.4.1:1883` for ESPs, `127.0.0.1:1883` on the Pi |
| Pi Ethernet IP | `192.168.2.11/24` |
| ATEM IP | `192.168.2.10` |
| Admin dashboard | `http://192.168.4.1:4321` |
| Client dashboard | `http://192.168.4.1:1234` |

Change Raspberry Pi server values in `src/RPI Python code/config/config.json` if your network uses different addresses. ESP firmware Wi-Fi and MQTT values are still compile-time settings in the Arduino sketch.

## Server Configuration

The Raspberry Pi server reads runtime settings from `src/RPI Python code/config/config.json`. Existing camera and tally assignments are stored in the same file, while server settings live under `Settings`:

```json
{
  "Settings": {
    "atem_ip": "192.168.2.10",
    "mqtt_host": "127.0.0.1",
    "mqtt_port": 1883,
    "admin_host": "0.0.0.0",
    "admin_port": 4321,
    "client_host": "0.0.0.0",
    "client_port": 1234,
    "camera_count": 8,
    "program_color": "#ff0000",
    "preview_color": "#00ff00",
    "off_color": "#000000",
    "identify_color": "#c832c8"
  }
}
```

Supported environment overrides:

| Environment variable | Setting |
| --- | --- |
| `TALLY_ATEM_IP` | ATEM switcher IP |
| `TALLY_MQTT_HOST` | MQTT broker host used by the Python server |
| `TALLY_MQTT_PORT` | MQTT broker port |
| `TALLY_ADMIN_HOST` | Admin dashboard bind address |
| `TALLY_ADMIN_PORT` | Admin dashboard port |
| `TALLY_CLIENT_HOST` | Client dashboard bind address |
| `TALLY_CLIENT_PORT` | Client dashboard port |
| `TALLY_CAMERA_COUNT` | Default number of cameras when no saved camera list exists |
| `TALLY_PROGRAM_COLOR` | Color for the active Program camera |
| `TALLY_PREVIEW_COLOR` | Color for the active Preview camera |
| `TALLY_OFF_COLOR` | Color for assigned cameras that are neither Program nor Preview |
| `TALLY_IDENTIFY_COLOR` | Temporary color used by the admin identify/test action |

Missing values fall back to the documented defaults. Invalid numeric values print a warning and fall back to the safe default for that setting.

## Raspberry Pi Setup

The project was tested on a Raspberry Pi 3B with Raspberry Pi OS Lite. When imaging the SD card, do not configure the Pi's Wi-Fi as a normal client network. The Pi needs `wlan0` for its own access point.

Connect to the Pi via Ethernet/SSH for the initial setup.

### 1. Update the System

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Dependencies

```bash
sudo apt install -y git python3-pip hostapd dnsmasq mosquitto mosquitto-clients
sudo apt install -y python3-paho-mqtt python3-flask python3-flask-socketio
```

Install the ATEM Python library:

```bash
python3 -m pip install PyATEMMax --break-system-packages
```

If your Raspberry Pi OS image does not allow `--break-system-packages`, create a virtual environment instead and run the project from that environment.

### 3. Install the Project Files

Clone the repository onto the Raspberry Pi:

```bash
git clone https://github.com/thescripter1/ESP_Tally_Lights.git ~/ESP_Tally_Lights
mkdir -p ~/tally-lights-server
cp -r ~/ESP_Tally_Lights/src/RPI\ Python\ code/* ~/tally-lights-server/
```

Run the server:

```bash
python3 ~/tally-lights-server/main.py
```

### 4. Configure the Wi-Fi Access Point

Create the `hostapd` configuration:

```bash
sudo nano /etc/hostapd/hostapd.conf
```

Use this configuration:

```ini
interface=wlan0
driver=nl80211
ssid=Tally-Lights
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

Tell `hostapd` where the configuration file is:

```bash
sudo nano /etc/default/hostapd
```

Set:

```bash
DAEMON_CONF="/etc/hostapd/hostapd.conf"
```

### 5. Configure DHCP for Wi-Fi Clients

Back up the default `dnsmasq` configuration:

```bash
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo nano /etc/dnsmasq.conf
```

Use:

```ini
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.50,255.255.255.0,24h
```

### 6. Assign a Static Wi-Fi IP to the Pi

On older Raspberry Pi OS images using `dhcpcd`, edit:

```bash
sudo nano /etc/dhcpcd.conf
```

Add:

```ini
interface wlan0
static ip_address=192.168.4.1/24
nohook wpa_supplicant
```

If your Raspberry Pi OS uses NetworkManager, configure `wlan0` through NetworkManager instead.

### 7. Enable the Access Point Services

```bash
sudo rfkill unblock all
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq
sudo systemctl restart hostapd
sudo systemctl restart dnsmasq
```

Reboot and check that the `Tally-Lights` Wi-Fi network appears:

```bash
sudo reboot
```

## MQTT Broker Setup

Mosquitto is used as the MQTT broker. Enable and start it:

```bash
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
```

Allow clients on the tally Wi-Fi network to connect:

```bash
sudo nano /etc/mosquitto/mosquitto.conf
```

Add or adjust:

```conf
listener 1883
allow_anonymous true
```

Restart Mosquitto:

```bash
sudo systemctl restart mosquitto
```

You can test MQTT locally on the Pi with two terminals:

```bash
mosquitto_sub -h 127.0.0.1 -t "tally/lights/#"
```

```bash
mosquitto_pub -h 127.0.0.1 -t "tally/lights/A" -m "#ff0000"
```

## Ethernet Setup for the ATEM

By default, the Python server connects to the ATEM at `192.168.2.10`. Set `Settings.atem_ip` or `TALLY_ATEM_IP` when your switcher uses another address. The documented Pi Ethernet address is `192.168.2.11/24`.

On Raspberry Pi OS images using NetworkManager, list connections:

```bash
sudo nmcli con show
```

Find the Ethernet connection name. It may be `Wired connection 1` or `eth0`. Then configure it:

```bash
sudo nmcli con modify "Wired connection 1" ipv4.addresses 192.168.2.11/24
sudo nmcli con modify "Wired connection 1" ipv4.gateway 192.168.2.1
sudo nmcli con modify "Wired connection 1" ipv4.dns "8.8.8.8 1.1.1.1"
sudo nmcli con modify "Wired connection 1" ipv4.method manual
sudo nmcli con up "Wired connection 1"
```

Verify:

```bash
ip addr show eth0
ping 192.168.2.10
```

If your connection has a different name, replace `Wired connection 1` with the name shown by `nmcli`.

## Running the Raspberry Pi Server

Start the server manually:

```bash
cd ~
python3 ~/tally-lights-server/main.py
```

The server starts three components using the values from `config/config.json`:

- Admin dashboard: `http://192.168.4.1:4321`
- Client dashboard: `http://192.168.4.1:1234`
- ATEM listener, connecting to `Settings.atem_ip`

Open the admin dashboard from a phone or laptop connected to the `Tally-Lights` Wi-Fi network. Use it to assign detected tally IDs to camera numbers.

### Optional systemd Service

Create a service so the server starts automatically:

```bash
sudo nano /etc/systemd/system/tally-lights.service
```

Use:

```ini
[Unit]
Description=ESP Tally Lights server
After=network-online.target mosquitto.service
Wants=network-online.target

[Service]
User=tally
WorkingDirectory=/home/tally/tally-lights-server
ExecStart=/usr/bin/python3 /home/tally/tally-lights-server/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tally-lights
sudo systemctl start tally-lights
sudo systemctl status tally-lights
```

## ESP8266 Firmware Setup

Open `src/Arduino Code/ESP_Tally_Light/ESP_Tally_Light.ino` in the Arduino IDE or PlatformIO.

Install these Arduino libraries:

- `ESP8266WiFi`
- `PubSubClient`
- `FastLED`

Before flashing each tally light, set its ID:

```cpp
#define character "A"
```

Each physical tally light needs a unique ID. The ID is used to build the MQTT topic:

```text
tally/lights/A
tally/lights/B
tally/lights/C
```

Check that the Wi-Fi and MQTT defaults match your Pi:

```cpp
const char* ssid = "Tally-Lights";
const char* password = "MeinSicheresPasswort";
const char* mqtt_server = "192.168.4.1";
```

The default LED setup is:

```cpp
#define LED_PIN D5
#define NUM_LEDS 4
#define BRIGHTNESS 5
#define LED_TYPE WS2812B
#define COLOR_ORDER GRB
```

Adjust these values to match your hardware.

## MQTT Topics and Color Commands

The ESP firmware accepts six-digit hex colors:

```text
#ff0000  Program/live by default
#00ff00  Preview/next by default
#000000  Off by default
#c832c8  Identify/mark light by default
```

When a camera is both Program and Preview, Program has priority. The Raspberry Pi server only sends a new MQTT color command when the target color for a tally light changes.

Topics:

| Topic | Direction | Purpose |
| --- | --- | --- |
| `tally/lights/<ID>` | Pi to ESP | Color command for one tally light |
| `tally/lights/status` | ESP to Pi | Heartbeat containing the ESP ID |

The admin dashboard uses the heartbeat topic to show available tally lights.

## Dashboards

Connect a device to the `Tally-Lights` Wi-Fi network and open:

- Admin: `http://192.168.4.1:4321`
- Client/live monitor: `http://192.168.4.1:1234`

The admin dashboard can assign tally IDs to camera numbers and briefly mark a selected light purple for identification. The client dashboard shows the current live camera and the configured camera list.

## Troubleshooting

### The Wi-Fi access point does not appear

Check:

```bash
sudo systemctl status hostapd
sudo systemctl status dnsmasq
rfkill list
ip addr show wlan0
```

Make sure `wlan0` is not blocked and has `192.168.4.1/24`.

### ESP connects to Wi-Fi but does not react

Check that Mosquitto is listening:

```bash
sudo systemctl status mosquitto
```

Subscribe to the ESP heartbeat topic:

```bash
mosquitto_sub -h 127.0.0.1 -t "tally/lights/status"
```

You should see the ESP ID every few seconds.

### The ATEM does not connect

Check that the ATEM is reachable from the Pi:

```bash
ping 192.168.2.10
```

If your ATEM uses another IP address, update `Settings.atem_ip` in `src/RPI Python code/config/config.json` or set `TALLY_ATEM_IP`.

### The Python server cannot find the config or chat file

The Python server reads `config/config.json` and `chats/chat.jsonl` relative to the Python source directory. Make sure those folders exist next to `main.py` and that the process user can write to them.

## Useful Links

- [PyATEMMax tally example](https://clvlabs.github.io/PyATEMMax/docs/examples/tally/)
- [Mosquitto documentation](https://mosquitto.org/documentation/)

## License

This project is licensed under the terms of the repository license.
