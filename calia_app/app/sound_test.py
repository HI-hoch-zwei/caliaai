# -*- coding: utf-8 -*-
# sound_test.py

import os
os.environ['SDL_AUDIODRIVER'] = 'directsound'

import pygame
import time

# ---- Konfiguration ----
# Wir probieren es mit expliziten, sehr kompatiblen Einstellungen
# Frequenz, Größe (-16 bedeutet signed 16-bit), Kanäle (2 für Stereo), Puffergröße
try:
    print("Initialisiere Pygame Mixer mit speziellen Einstellungen...")
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=4096)
    print("Pygame Mixer erfolgreich initialisiert.")
except Exception as e:
    print(f"FEHLER bei der Initialisierung von pygame.mixer: {e}")
    exit()

# Pfad zur Sound-Datei (relativ zum Skript)
sound_file = os.path.join("assets", "sounds", "activate.wav")

# ---- Testablauf ----
if not os.path.exists(sound_file):
    print(f"FEHLER: Sound-Datei nicht gefunden unter '{sound_file}'")
else:
    print(f"Lade Sound-Datei: {sound_file}")
    try:
        sound = pygame.mixer.Sound(sound_file)

        print("\nSpiele Sound ab...")
        sound.play()

        # Warten, bis der Sound zu Ende gespielt hat
        while pygame.mixer.get_busy():
            time.sleep(0.1)

        print("Sound-Wiedergabe beendet.")

    except Exception as e:
        print(f"FEHLER beim Laden oder Abspielen des Sounds: {e}")

pygame.quit()
print("\nTest beendet.")
