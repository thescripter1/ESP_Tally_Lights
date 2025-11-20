# ESP_Tally_Lights
A DIY Tally Light Project for Blackmagic ATEM Video Switchers, wich uses MQTT and an ESP 8266

#Architecture

If you want to build your own Version, you can 3D Print most of the parts. A rough part list can be found under CAD / Part-List

Setup of Raspberry Pi:
This Repo runs perfectly fine on a Raspberry Pi 3B with the Lite Os. I haven't tested the Desktop Version, but feel free to do so and let me know about your results.
Please note when you install the Lite OS Desktop version with the Raspberry Pi Imager Software, to not configure a WiFi setup. This will give you errors along the way.
1. Connect with the Raspberry Pi Command prompt, idealy via ssh.
   Update the System with: (sudo apt upgrade)
