# -*- coding: utf-8 -*-
# // -- Peter Luebke Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: Calia AI.
#
# calia_app.py
#
# Dies ist der HAUPT-Startpunkt für die Kivy Desktop-Anwendung (den Client).
# Sie lädt das "Gehirn" (CaliaLogic) und die GUI-Elemente.

import os
import sys
import datetime
import logging
import json
import re
import pygame
import threading
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# --- Kivy-Imports ---
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.clock import Clock, mainthread
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.core.window import Window
from kivy.animation import Animation

# --- Core-Imports (unsere neuen, sauberen Module) ---
from core.config_loader import (
    get_resource_path, 
    setup_logging, 
    load_config, 
    force_tensorflow_cpu, 
    VERSION
)
from core.calia_logic import CaliaLogic
try:
    from core.gui_widgets import (
        ShaderBackground, EqualizerWaveform, NexusCore, 
        SciFiPanel, SciFiLabel
    )
except ImportError as e:
    logging.critical(f"Konnte gui_widgets.py nicht importieren: {e}")

# --- Globale Initialisierung ---
force_tensorflow_cpu()
setup_logging()

# ==============================================================================
# ABSCHNITT 1: KIVY GUI-KLASSEN
# ==============================================================================

# Lade die .kv-Datei
Builder.load_file(get_resource_path('calia_gui.kv'))

class CaliaGUI(FloatLayout):
    """Die Root-Klasse für das Kivy-Layout (aus calia_gui.kv)."""
    status_text = StringProperty("SYSTEM: INITIALISIERE...")
    nexus_color = ListProperty([0.1, 0.7, 1, 1])
    nexus_rotation_angle = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pass

class CaliaApp(App):
    """
    Die Haupt-Kivy-App. Dient als "GUI-Controller" für CaliaLogic.
    Implementiert die Schnittstellen-Methoden (set_state, set_response etc.).
    """
    def build(self):
        logging.info("Kivy App 'build' Methode wird aufgerufen.")
        Window.size = (1200, 800)
        self.title = f"C.A.L.I.A. - Version {VERSION}"
        
        config = load_config()
        
        # WICHTIG: Wir übergeben 'self' (die App-Instanz) als den gui_controller
        self.logic = CaliaLogic(gui_controller=self, config=config)
        
        self.gui = CaliaGUI()
        self.active_popup = None
        self.teleprompter_animation = None
        
        Window.bind(on_keyboard=self._on_keyboard)
        Clock.schedule_once(lambda dt: self.logic.start_background_tasks(), 0.1)
        Clock.schedule_interval(self.update_context_label, 1.0)
        
        # WICHTIG: Der alte Flask-API-Server (run_api) wird hier NICHT mehr gestartet.
        # Diese App ist NUR der Client.
        
        logging.info("Kivy App 'build' Methode ist abgeschlossen.")
        return self.gui
    
    def on_stop(self):
        logging.info("Beende Calia...")
        if self.logic.pyaudio_instance:
            self.logic.pyaudio_instance.terminate()
            logging.info("PyAudio-Instanz beendet.")
    
    def _on_keyboard(self, window, key, scancode, codepoint, modifiers):
        """Verarbeitet globale Tastatur-Befehle."""
        if self.active_popup:
            if key == 27: # ESC
                self.active_popup.dismiss(); self.active_popup = None; return True
            return False # Eingaben blockieren, wenn Popup offen ist
            
        # Nur reagieren, wenn Calia bereit ist
        if self.logic.current_gui_state == 'idle':
            if codepoint == 'l': self.trigger_listening()
            elif codepoint == 't': self.show_text_input_popup()
            elif codepoint == 'x': self.show_help_popup()
            elif codepoint == 'p': self.show_personality_popup()
            
        if key == 32: # Leertaste (Audio stoppen)
            pygame.mixer.stop()
        elif key == 282: # F1 (Positives Feedback)
            self.logic.add_feedback_to_last_message(1)
        elif key == 283: # F2 (Negatives Feedback)
            self.logic.add_feedback_to_last_message(-1)
            
        return True
        
    def show_help_popup(self):
        content_text = ("[b]L[/b] - Spracheingabe starten\n[b]T[/b] - Texteingabe öffnen\n[b]X[/b] - Diese Hilfe anzeigen\n[b]P[/b] - Persönlichkeit wechseln\n\n"
                        "[b]Leertaste[/b] - Aktuelle Sprachausgabe stoppen\n[b]F1 / F2[/b] - Positives / Negatives Feedback geben\n[b]ESC[/b] - Pop-up schließen")
        self.active_popup = self._create_popup("Hilfe & Tastaturbefehle", content_text)
        self.active_popup.open()

    def show_personality_popup(self):
        content_text = "[b]Drücke die Zahl, um die Persönlichkeit zu wechseln:[/b]\n\n"
        try:
            keys = list(self.logic.personalities.keys())
            for i, key in enumerate(keys):
                name = self.logic.personalities[key].get('name', key.capitalize())
                prefix = "> " if self.logic.current_personality_prompt == self.logic.personalities[key].get('prompt') else "  "
                content_text += f"{prefix}[b]{i+1}[/b]: {name}\n"
        except Exception as e:
            content_text = f"Fehler beim Laden der Persönlichkeiten: {e}"
        self.active_popup = self._create_popup("Persönlichkeit wählen", content_text)
        self.active_popup.open()

    def show_text_input_popup(self):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        text_input = TextInput(multiline=False, font_size='20sp', focus=True)
        content.add_widget(text_input)
        button = Button(text='Senden', size_hint_y=None, height='48dp')
        content.add_widget(button)
        
        popup = Popup(title='Texteingabe', content=content, size_hint=(0.8, 0.4))
        
        def send_command(instance):
            command = text_input.text
            if command:
                self.logic.last_interaction_time = datetime.datetime.now(datetime.timezone.utc)
                # Starte die Verarbeitung im Logic-Thread
                threading.Thread(target=self.logic.process_command_router, args=(command,), daemon=True).start()
            popup.dismiss(); self.active_popup = None
            
        button.bind(on_press=send_command)
        text_input.bind(on_text_validate=send_command)
        
        self.active_popup = popup
        self.active_popup.open()

    def _create_popup(self, title, content_text):
        label = Label(text=content_text, font_size='18sp', markup=True)
        popup = Popup(title=title, content=label, size_hint=(0.7, 0.6))
        popup.bind(on_dismiss=lambda *args: setattr(self, 'active_popup', None))
        return popup

    # ==============================================================================
    # ABSCHNITT 2: GUI-CONTROLLER SCHNITTSTELLE (Implementierung)
    # ==============================================================================
    # Diese Methoden werden von CaliaLogic aufgerufen.
    # @mainthread stellt sicher, dass sie im Kivy-Thread ausgeführt werden.

    @mainthread
    def update_context_label(self, dt):
        """Aktualisiert die Uhrzeit/Ort-Anzeige."""
        if hasattr(self.gui, 'ids') and 'context_label' in self.gui.ids:
            try:
                tz_name = self.logic.user_profile.get('timezone', 'Europe/Berlin')
                location = self.logic.user_profile.get('location', 'Lüdenscheid').upper()
                user_tz = ZoneInfo(tz_name)
                now = datetime.datetime.now(user_tz)
                time_str = now.strftime('%H:%M:%S')
                date_str = now.strftime('%Y-%m-%d')
                self.gui.ids.context_label.text = f"LOCATION: {location} // {date_str} // TIME: {time_str}"
            except (ZoneInfoNotFoundError, AttributeError):
                self.gui.ids.context_label.text = "LOCATION: N/A // TIME: N/A"

    @mainthread
    def trigger_listening(self):
        """Startet den Zuhör-Prozess (wird von 'L' Taste ausgelöst)."""
        if self.logic.current_gui_state == 'idle':
            threading.Thread(target=self.logic.listen_and_process, daemon=True).start()

    @mainthread
    def set_waveform_amplitude(self, amplitude):
        """Leitet die Audio-Amplitude an das 'main_wave'-Widget weiter."""
        if hasattr(self.gui, 'ids') and 'main_wave' in self.gui.ids:
            self.gui.ids.main_wave.amplitude = amplitude

    @mainthread
    def set_state(self, state: str):
        """
        Aktualisiert den visuellen Zustand der GUI (Status-Text, Farben, Wellen-Modus).
        """
        self.logic.current_gui_state = state # Zustand in der Logik synchronisieren
        
        if self.teleprompter_animation:
            self.teleprompter_animation.cancel_all(self.gui.ids.response_scroller)
            self.teleprompter_animation = None
            
        main_wave = self.gui.ids.get('main_wave')
            
        if state == 'idle':
            self.gui.status_text = "STATUS: BEREIT\n'L' SPRECHEN | 'T' TEXT | 'X' HILFE"
            self.gui.nexus_color = [0.1, 0.5, 0.8, 1] 
            if main_wave: main_wave.mode = 'idle'
            
        elif state == 'listening': 
            self.gui.status_text = "STATUS: HÖRE ZU..."
            self.gui.nexus_color = [1, 0.5, 0, 1] 
            self.gui.ids.response_label.text = "" # Textfeld leeren
            if main_wave: main_wave.mode = 'listening'
            
        elif state == 'thinking': 
            self.gui.status_text = "STATUS: VERARBEITE DATEN..."
            self.gui.nexus_color = [0.7, 0, 1, 1] 
            if main_wave: main_wave.mode = 'thinking'
            
        elif state == 'speaking': 
            self.gui.status_text = "STATUS: AUDIOSYNTHESE AKTIV..."
            self.gui.nexus_color = [0, 1, 0.5, 1] 
            if main_wave: main_wave.mode = 'speaking'

    @mainthread
    def set_response(self, text: str, icon_code: str = None):
        """Zeigt den Antwort-Text in der GUI an und startet Teleprompter."""
        if self.teleprompter_animation:
            self.teleprompter_animation.cancel_all(self.gui.ids.response_scroller)
            self.teleprompter_animation = None
            
        clean_text = re.sub(r'(\*\*|\*|_)', '', text)
        self.gui.ids.response_label.text = clean_text
        Clock.schedule_once(self._start_scrolling, 0.1)

    def _start_scrolling(self, dt):
        """Startet die Auto-Scroll (Teleprompter)-Animation."""
        scroller = self.gui.ids.response_scroller
        label = self.gui.ids.response_label
        scroller.scroll_y = 1.0 # Nach ganz oben
        
        if label.height > scroller.height:
            pixels_to_scroll = label.height - scroller.height
            duration = max(2.0, pixels_to_scroll / 40.0) # Dauer basiert auf Textlänge
            self.teleprompter_animation = Animation(scroll_y=0, duration=duration)
            self.teleprompter_animation.start(scroller)

    @mainthread
    def change_theme(self, theme_name: str):
        """Ändert die Akzentfarbe der GUI."""
        logging.info(f"Theme-Änderung angefordert: {theme_name}")
        if theme_name == 'theme_warning': 
            self.gui.nexus_color = [1, 0.1, 0.1, 1]
        elif theme_name == 'theme_sunny': 
            self.gui.nexus_color = [1, 0.8, 0, 1]
        elif theme_name == 'theme_discovery':
            self.gui.nexus_color = [0.2, 0.9, 1, 1]

    @mainthread
    def propose_fact_to_learn(self, key: str, value: str):
        """
        NEU: Zeigt ein Popup an, um den Nutzer zu fragen, ob ein
        Fakt gelernt werden soll.
        """
        logging.info(f"Vorschlag zum Lernen erhalten: {key} = {value}")
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        label = Label(text=f"Soll ich mir folgendes merken?\n\n[b]{key}[/b]: {value}", 
                      markup=True, font_size='18sp')
        content.add_widget(label)
        
        button_layout = BoxLayout(size_hint_y=None, height='48dp', spacing=10)
        btn_yes = Button(text='Ja, merken')
        btn_no = Button(text='Nein, ignorieren')
        button_layout.add_widget(btn_yes)
        button_layout.add_widget(btn_no)
        content.add_widget(button_layout)
        
        popup = Popup(title='Fakt lernen', content=content, size_hint=(0.8, 0.4), auto_dismiss=False)
        
        def save_fact(instance):
            # Bestätigung an die Logik senden (direkter DB-Zugriff)
            self.logic.db_manager.update_user_profile_field(f"facts.{key}", value)
            self.logic.speak("In Ordnung, ich habe es mir gemerkt.")
            popup.dismiss(); self.active_popup = None

        def ignore_fact(instance):
            self.logic.speak("Okay, ignoriert.")
            popup.dismiss(); self.active_popup = None

        btn_yes.bind(on_press=save_fact)
        btn_no.bind(on_press=ignore_fact)
        
        self.active_popup = popup
        self.active_popup.open()


# ==============================================================================
# ABSCHNITT 3: STARTPUNKT DER ANWENDUNG
# ==============================================================================
if __name__ == '__main__':
    from dotenv import load_dotenv
    import nltk
    
    # .env laden (für API-Schlüssel)
    load_dotenv()
    
    # NLTK-Daten (für NLU) laden/prüfen
    try:
        portable_nltk_path = get_resource_path('nltk_data')
        if os.path.exists(portable_nltk_path):
            nltk.data.path.append(portable_nltk_path)
        nltk.download('punkt', quiet=True, download_dir=portable_nltk_path)
        nltk.download('wordnet', quiet=True, download_dir=portable_nltk_path)
    except Exception as e:
        logging.critical(f"Konnte NLTK-Daten nicht laden/finden: {e}")

    logging.info("Starte C.A.L.I.A. Kivy-Anwendung...")
    app = CaliaApp()
    
    logging.info("Starte Kivy Event-Loop (app.run). Die Konsole wird ab jetzt blockiert.")
    app.run()
