from shared_state import get_Pool
from tally import make_Farbe

import random

rainbow_colors = [
    "#FF0000",  # Rot
    "#FF7F00",  # Orange
    "#FFFF00",  # Gelb
    "#00FF00",  # Grün
    "#0000FF",  # Blau
    "#4B0082",  # Indigo
    "#8F00FF"   # Violett
]
import time

while True:
    pool = get_Pool()

    code = random.choice(rainbow_colors)
    print(code)

    for cam in pool:
        make_Farbe(cam, code)
    
    time.sleep(2)