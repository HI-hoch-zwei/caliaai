# -*- coding: utf-8 -*-
# // -- Okami Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.

import logging
from PIL import ImageGrab

class DesktopToolsPlugin:
    def __init__(self, logic_controller):
        self.logic = logic_controller

    def register(self):
        return {
            "capture_screenshot": self.capture_screenshot
        }

    def capture_screenshot(self):
        """
        Erstellt einen Screenshot des gesamten Bildschirms und speichert ihn intern
        für die weitere Analyse durch den Agenten.
        """
        try:
            logging.info("Erstelle Screenshot...")
            screenshot = ImageGrab.grab()
            self.logic.last_screenshot = screenshot # Speichere das Bildobjekt in der Hauptlogik
            return "Ein Screenshot wurde erfolgreich aufgenommen und steht für die Analyse bereit."
        except Exception as e:
            logging.error(f"Fehler beim Erstellen des Screenshots: {e}")
            self.logic.last_screenshot = None
            return "Fehler: Der Screenshot konnte nicht erstellt werden."
