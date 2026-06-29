#!/usr/bin/env bash
set -euo pipefail

SERVER_DIR="${SERVER_DIR:-$HOME/tally-lights-server}"
SERVICE_NAME="${SERVICE_NAME:-tally-lights}"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="${REPO_ROOT}/src/RPI Python code"
PYTHON_BIN="${PYTHON_BIN:-/usr/bin/python3}"

if [[ ! -d "${SOURCE_DIR}" ]]; then
  echo "Fehler: Server-Quellverzeichnis nicht gefunden: ${SOURCE_DIR}" >&2
  exit 1
fi

echo "Installiere apt-Abhaengigkeiten..."
sudo apt update
sudo apt install -y \
  python3-pip \
  python3-paho-mqtt \
  python3-flask \
  python3-flask-socketio \
  hostapd \
  dnsmasq \
  mosquitto \
  mosquitto-clients

echo "Installiere PyATEMMax, falls noch nicht vorhanden..."
if ! "${PYTHON_BIN}" - <<'PY' >/dev/null 2>&1
import PyATEMMax
PY
then
  "${PYTHON_BIN}" -m pip install PyATEMMax --break-system-packages
fi

echo "Kopiere Serverdateien nach ${SERVER_DIR}..."
mkdir -p "${SERVER_DIR}"
CONFIG_BACKUP="$(mktemp)"
CHAT_BACKUP="$(mktemp)"
CONFIG_EXISTS=0
CHAT_EXISTS=0
if [[ -f "${SERVER_DIR}/config/config.json" ]]; then
  cp "${SERVER_DIR}/config/config.json" "${CONFIG_BACKUP}"
  CONFIG_EXISTS=1
fi
if [[ -f "${SERVER_DIR}/chats/chat.jsonl" ]]; then
  cp "${SERVER_DIR}/chats/chat.jsonl" "${CHAT_BACKUP}"
  CHAT_EXISTS=1
fi
cp -a "${SOURCE_DIR}/." "${SERVER_DIR}/"
mkdir -p "${SERVER_DIR}/config" "${SERVER_DIR}/chats"
if [[ "${CONFIG_EXISTS}" -eq 1 ]]; then
  cp "${CONFIG_BACKUP}" "${SERVER_DIR}/config/config.json"
fi
if [[ "${CHAT_EXISTS}" -eq 1 ]]; then
  cp "${CHAT_BACKUP}" "${SERVER_DIR}/chats/chat.jsonl"
fi
rm -f "${CONFIG_BACKUP}" "${CHAT_BACKUP}"

echo "Erzeuge systemd-Service ${SERVICE_FILE}..."
sudo tee "${SERVICE_FILE}" >/dev/null <<SERVICE
[Unit]
Description=ESP Tally Lights server
After=network-online.target mosquitto.service
Wants=network-online.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${SERVER_DIR}
ExecStart=${PYTHON_BIN} ${SERVER_DIR}/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart mosquitto
sudo systemctl restart "${SERVICE_NAME}"

echo
echo "Installation abgeschlossen."
echo "Admin Dashboard:  http://192.168.4.1:4321"
echo "Client Dashboard: http://192.168.4.1:1234"
echo "Status pruefen:   sudo systemctl status ${SERVICE_NAME}"
