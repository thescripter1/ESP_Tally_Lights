# ESP Tally Lights

A DIY wireless tally light system for Blackmagic ATEM video switchers. A Raspberry Pi reads the current program input from the ATEM, publishes tally states over MQTT, and ESP8266-based tally lights subscribe to their assigned MQTT topics.

> [!WARNING]
> [!NOTE]
> Some code and variable names are still German. Runtime network and service settings are configured through `config/config.json` or environment variables.

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
| Friendly client URL | `http://tally.local` |

Change Raspberry Pi server values in `config/config.json` (next to `main.py` on the Pi, or `src/RPI Python code/config/config.json` in this repo) if your network uses different addresses. ESP firmware Wi-Fi and MQTT values are still compile-time settings in the Arduino sketch.

## Server Configuration

The Raspberry Pi server reads runtime settings from `config/config.json`. Existing camera and tally assignments are stored in the same file, while server settings live under `Settings`:

```json
{
  "Mode": "production",
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
    "identify_color": "#c832c8",
    "operating_mode": "production"
  }
}
```

`Mode` is the persisted current runtime mode. `production` connects to the real ATEM switcher, while `test` uses the built-in camera-change simulator. `Settings.operating_mode` is only the fallback used when no saved `Mode` exists yet.

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
| `TALLY_OPERATING_MODE` | Fallback mode when no saved `Mode` exists (`production` or `test`) |

Missing values fall back to the documented defaults. Invalid numeric values print a warning and fall back to the safe default for that setting.

## Raspberry Pi Setup

The project was tested on a Raspberry Pi 3B with Raspberry Pi OS Lite. When imaging the SD card, do not configure the Pi's Wi-Fi as a normal client network. The Pi needs `wlan0` for its own access point.

Connect to the Pi via Ethernet/SSH for the initial setup.

### Quick Server Install

Clone the repository and run the installer:

```bash
git clone https://github.com/thescripter1/ESP_Tally_Lights.git ~/ESP_Tally_Lights
cd ~/ESP_Tally_Lights
./scripts/install_rpi.sh
```

The script installs apt/Python dependencies, copies the Python server to `~/tally-lights-server`, creates runtime folders, installs a `tally-lights.service` systemd unit, enables it, starts Mosquitto, and restarts the tally server. It is safe to re-run; existing `config/config.json` remains in the server directory and is reused.

Override the install target or service name if needed:

```bash
SERVER_DIR=/opt/tally-lights-server SERVICE_NAME=tally-lights ./scripts/install_rpi.sh
```

After installation:

```bash
sudo systemctl status tally-lights
```

Then continue with the Wi-Fi access point and Ethernet setup sections below if the Pi network has not been configured yet.

### Manual Install

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
bind-interfaces

dhcp-range=192.168.4.10,192.168.4.50,255.255.255.0,24h
dhcp-option=option:router,192.168.4.1
dhcp-option=option:dns-server,192.168.4.1
```

This makes Wi-Fi clients use the Raspberry Pi as their router and DNS server. The friendly client URL uses the Raspberry Pi's mDNS/Avahi hostname in step 8 because Apple devices handle `.local` names reliably in Safari.

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

### 8. Add Friendly Dashboard URLs

The client dashboard runs on port `1234`, but users should not have to type that port. Use the Raspberry Pi's Avahi/mDNS hostname for the Safari-friendly `.local` name, then redirect port `80` to the already running Flask client server.

The resulting client URL is:

```text
http://tally.local
```

Avoid private pseudo-TLDs such as `.lan` for this. Some browsers, especially Safari, may treat unknown suffixes as a search query unless the user types the full URL perfectly.

First make sure Avahi is running and the Pi hostname is `tally`:

```bash
hostname
cat /etc/hostname
sudo systemctl status avahi-daemon
```

The hostname should be:

```text
tally
```

If you change the hostname, restart Avahi:

```bash
sudo systemctl restart avahi-daemon
```

Then redirect normal HTTP traffic to the existing dashboard ports. The client dashboard is reachable at `http://tally.local`; the admin dashboard remains reachable at `http://tally.local:4321`.

Create the helper script:

```bash
sudo nano /usr/local/sbin/tally-dns-shortcuts.sh
```

Use:

```sh
#!/bin/sh
set -eu

WIFI_IF="${WIFI_IF:-wlan0}"
WIFI_IP="${WIFI_IP:-192.168.4.1}"
LAN_IP="${LAN_IP:-192.168.2.11}"
CLIENT_IP="${CLIENT_IP:-192.168.4.2}"
ADMIN_PORT="${ADMIN_PORT:-4321}"
CLIENT_PORT="${CLIENT_PORT:-1234}"

ensure_alias() {
    if ! ip -4 addr show dev "$WIFI_IF" | grep -q "${CLIENT_IP}/24"; then
        ip addr add "${CLIENT_IP}/24" dev "$WIFI_IF"
    fi
}

ensure_rule() {
    chain="$1"
    dest_ip="$2"
    dest_port="$3"
    target_port="$4"

    if ! iptables -t nat -C "$chain" -p tcp -d "$dest_ip" --dport "$dest_port" -j REDIRECT --to-ports "$target_port" 2>/dev/null; then
        iptables -t nat -A "$chain" -p tcp -d "$dest_ip" --dport "$dest_port" -j REDIRECT --to-ports "$target_port"
    fi
}

remove_rule() {
    chain="$1"
    dest_ip="$2"
    dest_port="$3"
    target_port="$4"

    while iptables -t nat -C "$chain" -p tcp -d "$dest_ip" --dport "$dest_port" -j REDIRECT --to-ports "$target_port" 2>/dev/null; do
        iptables -t nat -D "$chain" -p tcp -d "$dest_ip" --dport "$dest_port" -j REDIRECT --to-ports "$target_port"
    done
}

remove_http_rules() {
    chain="$1"
    dest_ip="$2"

    remove_rule "$chain" "$dest_ip" 80 "$ADMIN_PORT"
    remove_rule "$chain" "$dest_ip" 80 "$CLIENT_PORT"
}

case "${1:-start}" in
    start)
        ensure_alias
        remove_http_rules PREROUTING "$WIFI_IP"
        remove_http_rules PREROUTING "$LAN_IP"
        remove_http_rules PREROUTING "$CLIENT_IP"
        remove_http_rules OUTPUT "$WIFI_IP"
        remove_http_rules OUTPUT "$LAN_IP"
        remove_http_rules OUTPUT "$CLIENT_IP"
        ensure_rule PREROUTING "$WIFI_IP" 80 "$CLIENT_PORT"
        ensure_rule PREROUTING "$LAN_IP" 80 "$CLIENT_PORT"
        ensure_rule PREROUTING "$CLIENT_IP" 80 "$CLIENT_PORT"
        ensure_rule OUTPUT "$WIFI_IP" 80 "$CLIENT_PORT"
        ensure_rule OUTPUT "$LAN_IP" 80 "$CLIENT_PORT"
        ensure_rule OUTPUT "$CLIENT_IP" 80 "$CLIENT_PORT"
        ;;
    stop)
        remove_http_rules PREROUTING "$WIFI_IP"
        remove_http_rules PREROUTING "$LAN_IP"
        remove_http_rules PREROUTING "$CLIENT_IP"
        remove_http_rules OUTPUT "$WIFI_IP"
        remove_http_rules OUTPUT "$LAN_IP"
        remove_http_rules OUTPUT "$CLIENT_IP"
        ip addr del "${CLIENT_IP}/24" dev "$WIFI_IF" 2>/dev/null || true
        ;;
    restart)
        "$0" stop
        "$0" start
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}" >&2
        exit 2
        ;;
esac
```

Enable it:

```bash
sudo chmod 755 /usr/local/sbin/tally-dns-shortcuts.sh
sudo nano /etc/systemd/system/tally-dns-shortcuts.service
```

Use:

```ini
[Unit]
Description=Tally Lights friendly DNS URL shortcuts
After=network-online.target dnsmasq.service
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/tally-dns-shortcuts.sh start
ExecStop=/usr/local/sbin/tally-dns-shortcuts.sh stop

[Install]
WantedBy=multi-user.target
```

Then start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tally-dns-shortcuts.service
sudo systemctl restart tally-dns-shortcuts.service
```

After reconnecting to the `Tally-Lights` Wi-Fi network, these URLs should work:

```text
http://tally.local
http://tally.local:4321
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
- ATEM listener in `production` mode, connecting to `Settings.atem_ip`

Open the admin dashboard from a phone or laptop connected to the `Tally-Lights` Wi-Fi network. Use it to assign detected tally IDs to camera numbers. The mode selector in the admin header switches between the real ATEM listener and the test simulator without restarting the server.

### Optional systemd Service

A systemd service starts the Python server automatically when the Pi boots. This is the recommended setup once the server works manually.

```bash
sudo nano /etc/systemd/system/tally-lights.service
```

Use the example below, but make sure `WorkingDirectory` and `ExecStart` match the directory where you copied the Python server. If you used the copy command from this README, the path is `/home/tally/tally-lights-server/main.py`.

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

If you use a virtual environment, point `ExecStart` to that Python interpreter instead:

```ini
ExecStart=/home/tally/.venv/bin/python /home/tally/tally-lights-server/main.py
```

Enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tally-lights
sudo systemctl start tally-lights
sudo systemctl status tally-lights
```

Verify that the dashboards are actually listening:

```bash
ss -ltnp | grep -E ':4321|:1234'
curl -I http://127.0.0.1:4321/
curl -I http://127.0.0.1:1234/
```

Both `curl` commands should return `HTTP/1.1 200 OK`.

View the service logs with `journalctl`. To show all logs from the current boot and then keep following new log lines live, use:

```bash
journalctl -u tally-lights -b -n all -f
```

Press `Ctrl+C` to leave the live log view. This only stops `journalctl`; it does not stop the Python server. If you only want the most recent log lines and then live updates, use:

```bash
journalctl -u tally-lights -b -n 100 -f
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

## Runtime Resilience

The Raspberry Pi server reconnects to MQTT automatically and subscribes to the tally light heartbeat topic again after reconnect. The ATEM listener also retries after connection loss or switcher reboot without requiring a Python server restart.

ESP tally lights send a heartbeat every 10 seconds. The admin dashboard marks a light offline when no heartbeat has been received for 30 seconds. When Wi-Fi or MQTT comes back, ESP lights reconnect and resubscribe to their `tally/lights/<ID>` topic.

## Dashboards

Connect a device to the `Tally-Lights` Wi-Fi network and open:

- Admin: `http://192.168.4.1:4321`
- Client/live monitor: `http://192.168.4.1:1234`

The admin dashboard can assign tally IDs to camera numbers and briefly mark a selected light purple for identification. The client dashboard shows the current live camera and the configured camera list.

## Troubleshooting

### Dashboard pages are not reachable

First check whether the Python server is running:

```bash
sudo systemctl status tally-lights
journalctl -u tally-lights -n 100 --no-pager
ss -ltnp | grep -E ':4321|:1234'
```

For a full live startup log from the current boot, use:

```bash
journalctl -u tally-lights -b -n all -f
```

The `-f` option follows new log lines, and `-n all` prevents `journalctl` from showing only the default last 10 lines before entering live mode.

If `ss` does not show `0.0.0.0:4321` and `0.0.0.0:1234`, the dashboard servers are not running. 
When testing in a browser, use plain HTTP:

```text
http://192.168.4.1:4321
http://192.168.4.1:1234
```

Do not use `https://` unless you have explicitly configured TLS. If the Python log shows unreadable request bytes followed by `Bad request version`, a browser or device is trying HTTPS against the HTTP-only Flask server.

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
