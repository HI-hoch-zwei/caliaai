# -*- coding: utf-8 -*-
# // -- Peter Luebke Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: Calia AI.
#
# web_server.py
#
# Dies ist der HAUPT-Startpunkt für den Headless-Server (z.B. auf simplepod.ai).
# Er lädt CaliaLogic mit einem "Mock-Controller" und startet die FastAPI.

import threading
import time
import logging
import queue # NEU: Für robustes Warten auf Antworten

from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel

# --- Core-Imports (unsere neuen, sauberen Module) ---
# WICHTIG: Die Imports wurden korrigiert
from core.calia_logic import CaliaLogic
from core.config_loader import load_config, setup_logging

# --- Logging sofort initialisieren ---
setup_logging()

# --- Die Brücke zwischen Webserver und Desktop-Logik ---

class MockGuiController:
    """
    Ein Dummy-GUI-Controller, der die Methoden der echten GUI simuliert,
    aber die Aufrufe ins Leere (oder ins Server-Log) laufen lässt.
    """
    def __init__(self):
        self.current_state = "idle"
        self.is_headless = True # NEU: Signalisiert der Logik den Server-Modus

    def set_state(self, new_state: str):
        # Logge den Statuswechsel, statt ihn anzuzeigen
        logging.info(f"[MockGUI]: Zustand geändert zu -> {new_state}")
        self.current_state = new_state

    def play_sound(self, sound_name: str):
        # Im Backend spielen wir keine UI-Sounds ab
        pass

    def set_response(self, text: str, icon_code: str = None):
        # Diese Methode wird für die API-Antwort nicht mehr benötigt,
        # da wir die 'speak'-Funktion direkt abfangen (siehe unten).
        logging.info(f"[MockGUI]: Antwort empfangen -> '{text[:50]}...'")
        pass
    
    # --- Fehlende Methoden aus der Schnittstelle hinzufügen ---
    
    def set_waveform_amplitude(self, amplitude: float):
        # Wird im Headless-Modus nicht benötigt
        pass

    def change_theme(self, theme_name: str):
        # Wird im Headless-Modus nicht benötigt
        logging.info(f"[MockGUI]: Theme-Wechsel ignoriert -> {theme_name}")
        pass

    def propose_fact_to_learn(self, key: str, value: str):
        # Wird im Headless-Modus nicht benötigt.
        # Die Logik (in CaliaLogic) wird dies erkennen und den Fakt
        # dank `is_headless = True` automatisch speichern.
        pass


# --- FastAPI-Anwendung initialisieren ---
app = FastAPI(
    title="C.A.L.I.A. AI API",
    description="API-Endpunkt für das Calia-Backend.",
    version=load_config().get("VERSION", "0.9.32-Refactored") # Version aus config laden
)

# Definiere, wie eine Anfrage vom Frontend aussehen muss
class Question(BaseModel):
    text: str
    # Zukünftig: optional user_id: str

# --- Calia einmalig beim Serverstart laden ---
logging.info("Lade Calia-Konfiguration für den Webserver...")
config = load_config()
mock_gui = MockGuiController()

# Wir übergeben den Dummy-Controller an Calia. Jetzt kann sie ohne Kivy/Pygame laufen!
# (Pygame wird in CaliaLogic zwar noch für mixer.init() geladen, aber nicht für die GUI)
calia_logic = CaliaLogic(gui_controller=mock_gui, config=config)

# Starte die Hintergrund-Initialisierung (TTS, NLU etc.)
logging.info("Starte Calia-Backend-Initialisierung im Hintergrund...")
calia_logic.start_background_tasks()
logging.info("Calia-Backend ist bereit und wartet auf Anfragen.")


# --- Unsere API-Endpunkte ---

@app.get("/", summary="Server-Status")
def read_root():
    """Ein einfacher Test-Endpunkt, um zu sehen, ob der Server läuft."""
    return {"message": "Calia Webserver ist online. Bereit für Anfragen an /ask"}

@app.post("/ask", summary="Frage an Calia stellen")
async def ask_calia(question: Question):
    """
    Der Haupt-Endpunkt, um Calia eine Frage zu stellen.
    Dieser Endpunkt fängt die 'speak'-Funktion von Calia ab,
    um die Antwort direkt als HTTP-Response zurückzugeben.
    """
    logging.info(f"Anfrage an /ask erhalten: '{question.text}'")
    
    response_queue = queue.Queue()

    # 1. Temporäre Speak-Funktion, die in unsere Queue schreibt
    def speak_wrapper(text: str, is_startup_message: bool = False):
        logging.info(f"Antwort für API abgefangen: '{text[:50]}...'")
        response_queue.put(text)
        # WICHTIG: Den Zustand der Logik trotzdem zurücksetzen
        calia_logic.gui.set_state('idle') 
    
    # 2. Monkey-Patching: Ersetze die echte Speak-Funktion durch unsere
    original_speak = calia_logic.speak
    calia_logic.speak = speak_wrapper
    
    response_text = ""
    try:
        # 3. Starte die Verarbeitung.
        # process_command_router läuft synchron, bis 'speak_wrapper' aufgerufen wird.
        calia_logic.process_command_router(question.text)
        
        # 4. Warte auf die Antwort aus der Queue (mit Timeout)
        response_text = response_queue.get(timeout=20.0) # 20s Timeout
        
    except queue.Empty:
        logging.error(f"Verarbeitung für '{question.text}' timed out (20s)")
        response_text = "Calia hat nicht rechtzeitig geantwortet. Die Aufgabe war eventuell zu komplex."
    except Exception as e:
        logging.critical(f"Schwerer Fehler bei der Verarbeitung von /ask: {e}", exc_info=True)
        response_text = f"Ein interner Serverfehler ist aufgetreten: {e}"
    finally:
        # 5. WICHTIG: Die Originalfunktion in jedem Fall wiederherstellen!
        calia_logic.speak = original_speak

    return {"user_question": question.text, "calia_response": response_text}

# --- Den Server starten ---
if __name__ == "__main__":
    # Dieser Befehl startet den Webserver auf deinem Computer
    # Auf simplepod.ai wird dies oft automatisch vom Hoster übernommen
    logging.info("Starte FastAPI-Server mit Uvicorn auf http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)