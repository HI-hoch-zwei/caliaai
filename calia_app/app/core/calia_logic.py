# -*- coding: utf-8 -*-
# // -- Peter Luebke Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: Calia AI.
#
# core/calia_logic.py
#
# Das "Gehirn" von Calia. Diese Klasse enthält die gesamte Kernlogik
# und ist 100% unabhängig von der GUI (Kivy).

import os
import sys
import datetime
import logging
import json
import queue
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import threading
import time
import math
import random
import re
import pygame
import numpy as np
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
try:
    import pvporcupine
except ImportError:
    pvporcupine = None
try:
    import pyaudio
except ImportError:
    logging.critical("PyAudio fehlt! Echtzeit-Wellenform wird nicht funktionieren.")
    pyaudio = None
import speech_recognition as sr

# --- Interne Core-Imports ---
from core.config_loader import get_resource_path
from core.nlu_processor import NLUProcessor
from core.plugin_manager import PluginManager
from core.database_manager import DatabaseManager
from core.tts_manager import TTSManager
from core.service_manager import ServiceManager

AVAILABLE_VOICES = {"weiblich standard": "de-DE-Wavenet-F", "männlich studio": "de-DE-Studio-C"}

class CaliaLogic:
    def __init__(self, gui_controller, config):
        """
        Initialisiert das Gehirn.
        
        :param gui_controller: Ein Objekt (z.B. die CaliaApp oder ein MockGuiController),
                               das die Methoden set_state, set_response etc. implementiert.
        :param config: Das geladene config.json-Dictionary.
        """
        logging.info("Erstelle CaliaLogic-Instanz (das Gehirn)...")
        self.gui = gui_controller # WICHTIG: Umbenannt von kivy_app zu gui_controller
        self.config = config
        self.script_dir = get_resource_path(".")
        self.state_lock = threading.Lock()
        self.thought_queue = queue.Queue()
        self.current_gui_state = 'idle' 
        
        # Manager-Instanzen
        self.db_manager = DatabaseManager()
        self.service_manager = ServiceManager(config=self.config, script_dir=self.script_dir)
        self.tts_manager = None
        self.nlu_processor = None
        self.plugin_manager = None
        
        # Service-Clients
        self.calendar_service = None
        self.openai_client = None
        self.tts_client = None

        # Profil & Status
        self.llm_cache = {}
        self.cache_ttl_seconds = 3600
        self.user_profile = {}
        self.current_voice_key = self.config.get("DEFAULT_VOICE_KEY", "weiblich standard")
        self.personalities = {}
        self.current_personality_prompt = ""
        self.last_interaction_time = datetime.datetime.now(datetime.timezone.utc)
        self.last_weather_icon_code = None
        self.warned_event_ids = set()
        self.active_llm = 'openai'
        self.politeness_buffer_seconds = self.config.get("POLITENESS_BUFFER_SECONDS", 5)
        self.cognitive_tasks = {}
        self.pyaudio_instance = None
        self.last_weather_check_date = None
        self.force_llm_for_intents = self.config.get("FORCE_LLM_FOR_INTENTS", [])
        self.pygame_sounds = {}
        
        self._setup_cognitive_tasks()
        logging.info("CaliaLogic-Instanz wurde erstellt.")

    def start_background_tasks(self):
        """Startet die schwere Initialisierung (Audio, TTS, AI) in einem Thread."""
        logging.info("Starte Hintergrund-Thread für Backend-Initialisierung.")
        threading.Thread(target=self._initialize_calia_backend, daemon=True).start()

    def _initialize_calia_backend(self):
        logging.info("Backend-Initialisierung gestartet (Hintergrund-Thread).")
        try:
            logging.info("Initialisiere Pygame-Mixer...")
            pygame.mixer.pre_init(44100, -16, 2, 512)
            pygame.mixer.init()
            self.pygame_sounds = self._load_pygame_sounds()
            logging.info("Pygame-Mixer erfolgreich initialisiert.")
            
            if pyaudio:
                self.pyaudio_instance = pyaudio.PyAudio()
                logging.info("PyAudio-Instanz erfolgreich initialisiert.")
            else:
                logging.error("PyAudio konnte nicht geladen werden. Echtzeit-Audio fällt aus.")
            
            logging.info("Initialisiere Kernsysteme...")
            self.tts_client = self.service_manager.init_google_tts()
            if self.tts_client:
                self.tts_manager = TTSManager(tts_client=self.tts_client, available_voices=AVAILABLE_VOICES)
            else:
                logging.error("TTS-Client konnte nicht geladen werden. Calia wird stumm bleiben.")
            
            # Erste Sprachausgabe (nur wenn TTS verfügbar)
            self.speak(random.choice(["Systeme werden gestartet...", "Bin gleich für dich da."]), is_startup_message=True)
            
            self.calendar_service = self.service_manager.init_calendar()
            self.openai_client = self.service_manager.init_openai()
            self.user_profile = self.db_manager.load_user_profile()
            
            try:
                self.nlu_processor = NLUProcessor(
                    intents_file=get_resource_path('initial_intents.json'),
                    model_file=get_resource_path('calia_model.keras'),
                    words_file=get_resource_path('words.pkl'),
                    classes_file=get_resource_path('classes.pkl')
                )
            except Exception as e:
                logging.critical(f"NLU Prozessor konnte nicht geladen werden: {e}")
            
            self.plugin_manager = PluginManager(plugin_folder=get_resource_path('plugins'), logic_controller=self)
            self.plugin_manager.load_plugins()
            self._load_personalities()
            
            logging.info("Alle Systeme sind initialisiert und bereit.")
            self._announce_full_readiness() 
            threading.Thread(target=self._consciousness_loop, daemon=True).start()
        except Exception as e:
            logging.critical(f"FATALER FEHLER während der Backend-Initialisierung: {e}", exc_info=True)
    
    def _load_pygame_sounds(self):
        """Lädt Sound-Effekte in den Speicher."""
        sounds = {}
        # Pfade korrigiert (kein 'assets.' am Anfang)
        sound_files = {
            'activate': 'assets/sounds/activate.wav', 
            'confirm': 'assets/sounds/confirm.wav', 
            'suggestion': 'assets/sounds/suggestion.wav', 
            'error': 'assets/sounds/error.mp3'
        }
        for name, path in sound_files.items():
            full_path = get_resource_path(path)
            if os.path.exists(full_path):
                try: 
                    sounds[name] = pygame.mixer.Sound(full_path)
                except Exception as e: 
                    logging.error(f"Pygame Sound Ladefehler '{path}': {e}")
            else:
                logging.warning(f"Sound-Datei nicht gefunden: {full_path}")
        return sounds

    def _play_sound(self, sound_name: str):
        """Spielt einen geladenen Sound-Effekt ab."""
        if sound_name in self.pygame_sounds:
            self.pygame_sounds[sound_name].play()

    def _execute_llm_call(self, system_prompt: str, user_prompt: str, is_json_output: bool = False):
        """Führt einen gecachten LLM-Aufruf (OpenAI) aus."""
        cache_key = f"{system_prompt}|{user_prompt}|{is_json_output}"
        if cache_key in self.llm_cache:
            entry = self.llm_cache[cache_key]
            if time.time() - entry['timestamp'] < self.cache_ttl_seconds:
                return entry['response']
        
        if not self.openai_client:
            logging.error("OpenAI-Client nicht verfügbar für LLM-Aufruf.")
            return None
            
        try:
            messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
            api_params = {"model": "gpt-4o", "messages": messages}
            if is_json_output:
                api_params["response_format"] = {"type": "json_object"}
            
            completion = self.openai_client.chat.completions.create(**api_params)
            response = completion.choices[0].message.content
            self.llm_cache[cache_key] = {'response': response, 'timestamp': time.time()}
            return response
        except Exception as e:
            logging.error(f"OpenAI LLM-Aufruf fehlgeschlagen: {e}")
            return None

    def _clean_text_for_tts(self, text: str) -> str:
        """Entfernt Markdown etc. aus Text für eine saubere Sprachausgabe."""
        text = re.sub(r'(\*\*|\*|_)', '', text) # Markdown (fett, kursiv)
        text = re.sub(r'^\s*#+\s*', '', text, flags=re.MULTILINE) # Markdown (Überschriften)
        return text

    def speak(self, text: str, is_startup_message: bool = False):
        """
        Der Haupt-Endpunkt für alle Sprachausgaben.
        Aktualisiert den GUI-Status und startet die TTS-Synthese.
        """
        if not text:
            self.gui.set_state('idle')
            return
            
        self.last_interaction_time = datetime.datetime.now(datetime.timezone.utc)
        self._check_context_for_theme_change(text)
        
        # Direkter, expliziter Aufruf an den Controller
        self.gui.set_state('speaking')
        self.gui.set_response(text=text, icon_code=self.last_weather_icon_code)
        self.last_weather_icon_code = None
        
        if not is_startup_message:
            self.db_manager.add_to_history("assistant", text)
            
        if self.tts_manager:
            clean_text = self._clean_text_for_tts(text)
            # Die Callback-Funktion ruft direkt die GUI-Methode auf
            on_done_callback = lambda: self.gui.set_state('idle')
            threading.Thread(
                target=self.tts_manager.synthesize_and_play, 
                args=(clean_text, self.current_voice_key, on_done_callback), 
                daemon=True
            ).start()
        else:
            # Fallback, wenn kein TTS verfügbar ist (z.B. Server-Mock)
            time.sleep(0.1) # Simuliere Arbeit
            self.gui.set_state('idle')

    def listen_and_process(self, image_path: str = None):
        """
        Startet den Zuhör-Vorgang (PyAudio-Loop) und leitet das
        Ergebnis an den Command-Router weiter.
        """
        if not self.pyaudio_instance:
            self.speak("Entschuldigung, mein Audiosystem ist nicht initialisiert.")
            self.gui.set_state('idle')
            return
            
        self._play_sound('activate')
        self.gui.set_state('listening')
        
        recognizer = sr.Recognizer()
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        SILENCE_THRESHOLD_RMS = 300 # Empfindlichkeit der Stille-Erkennung
        SILENCE_DURATION = 1.5 # Sekunden der Stille, bis Aufnahme stoppt
        
        frames = []
        silent_chunks = 0
        chunks_per_second = RATE / CHUNK
        
        try:
            stream = self.pyaudio_instance.open(
                format=FORMAT, 
                channels=CHANNELS, 
                rate=RATE, 
                input=True, 
                frames_per_buffer=CHUNK
            )
        except Exception as e:
            logging.error(f"Pyaudio stream error: {e}")
            self.gui.set_state('idle')
            self.speak("Entschuldigung, ich habe ein Problem mit meinem Mikrofon.")
            return

        logging.info("Höre zu (mit Echtzeit-Visualisierung)...")
        
        # Zuhör-Schleife (blockiert den Thread)
        while self.current_gui_state == 'listening':
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                frames.append(data)
                audio_chunk = np.frombuffer(data, dtype=np.int16)
                rms = np.sqrt(np.mean(np.square(audio_chunk.astype(np.float64))))
                
                # Amplitude normalisieren (logarithmisch) für die GUI-Welle
                if rms > 0:
                    normalized_amp = (math.log10(rms) / 4.5) * 1.5
                    normalized_amp = max(0, min(1, normalized_amp))
                else:
                    normalized_amp = 0.0
                
                # Direkter Aufruf an den GUI-Controller
                self.gui.set_waveform_amplitude(normalized_amp)
                
                # Stille-Erkennung
                if rms < SILENCE_THRESHOLD_RMS:
                    silent_chunks += 1
                else:
                    silent_chunks = 0
                    
                if (silent_chunks / chunks_per_second) > SILENCE_DURATION:
                    logging.info("Stille erkannt, beende Aufnahme.")
                    break
                    
            except IOError as e:
                # [Errno -9981] Input overflowed (passiert, wenn OS zu langsam)
                logging.warning(f"Audio stream read error (IOError): {e}")
                continue 
            except Exception as e:
                logging.error(f"Fehler in der Audio-Schleife: {e}")
                break
                
        logging.info("Aufnahme beendet, verarbeite...")
        stream.stop_stream()
        stream.close()
        self.gui.set_state('thinking')
        
        if not frames:
            logging.warning("Keine Audiodaten aufgenommen.")
            self.gui.set_state('idle')
            return
            
        audio_data = sr.AudioData(b''.join(frames), RATE, 2)
        
        # Sprach-Erkennung (Google)
        try:
            query = recognizer.recognize_google(audio_data, language='de-DE')
            logging.info(f"Erkannt: '{query}'")
            self.last_interaction_time = datetime.datetime.now(datetime.timezone.utc)
            self.process_command_router(query.lower(), image_path=image_path)
        except sr.UnknownValueError:
            logging.warning("Sprache nicht verstanden.")
            self.gui.set_state('idle') # Zurück zu Bereit
        except Exception as e:
            logging.error(f"Spracherkennungsfehler: {e}")
            self.gui.set_state('idle')

    def _reset_conversation_context(self):
        """Setzt den Konversationsverlauf zurück."""
        logging.info("Chat-Kontext wurde auf Anfrage zurückgesetzt.")
        # TODO: Evtl. DB-Historie hier als "abgeschlossen" markieren
        self.speak("Okay, verstanden. Worüber möchtest du jetzt sprechen?")

    def process_command_router(self, command: str, image_path: str = None):
        """
        Der Haupt-Router. Nimmt einen Befehl entgegen, prüft auf NLU-Intents
        und leitet ihn ansonsten an das generative LLM weiter.
        """
        self.last_interaction_time = datetime.datetime.now(datetime.timezone.utc)
        
        # Kontext-Reset prüfen
        reset_keywords = ["neues thema", "vergiss das", "lass uns über etwas anderes sprechen", "thema wechseln"]
        if any(keyword in command for keyword in reset_keywords):
            self._reset_conversation_context()
            return

        # Im DB-Verlauf speichern
        self.db_manager.add_to_history("user", command if not image_path else f"[Bild gesendet] {command}")
        self.gui.set_state('thinking')
        
        # 1. NLU-Prüfung (Lokales Modell)
        predicted_intents = self.nlu_processor.predict_intent(command) if self.nlu_processor else None
        
        # 2. Intent ausführen oder an LLM übergeben
        if predicted_intents and predicted_intents[0]['intent'] not in self.force_llm_for_intents:
            intent_tag = predicted_intents[0]['intent']
            logging.info(f"NLU-Intent erkannt: {intent_tag}")
            self.speak(self.nlu_processor.get_response(intent_tag))
        else:
            # 3. Generative Verarbeitung (LLM)
            logging.info("Kein lokaler Intent (oder LLM erzwungen). Leite an LLM weiter.")
            self._process_generative_command(command, image_path=image_path)

    def _process_generative_command(self, command: str, image_path: str = None, output_format: str = 'text'):
        """Verarbeitet einen Befehl mit dem OpenAI LLM."""
        if image_path:
            self.speak("Die Bildverarbeitung ist in diesem Modus noch nicht implementiert.")
            # Hier käme die Logik für GPT-4-Vision hin
        
        history = self.db_manager.get_recent_history(num_messages=10)
        history_str = "\n".join([f"{m['role']}: {m['content']}" for m in history])
        user_prompt = f"Aktueller Gesprächsverlauf als Kontext:\n{history_str}\n\nNeue Nutzereingabe:\n{command}"
        
        is_json = (output_format == 'json')
        final_answer = self._execute_llm_call(self.current_personality_prompt, user_prompt, is_json)
        
        if not final_answer:
            error_msg = "Entschuldigung, meine künstliche Intelligenz konnte keine Antwort generieren."
            if is_json: 
                return {"responseText": error_msg, "action": "error"}
            else: 
                self.speak(error_msg)
            return
            
        if is_json:
            try: 
                return json.loads(final_answer)
            except json.JSONDecodeError: 
                return {"responseText": "Antwort war nicht im korrekten Format.", "action": "error"}
        else:
            self.speak(final_answer)
    
    def _load_personalities(self):
        """Lädt die Persönlichkeitsprofile aus der personalities.json."""
        try:
            with open(get_resource_path('personalities.json'), 'r', encoding='utf-8') as f: 
                self.personalities = json.load(f)
            # Führe den Befehl 'change_personality' aus dem Plugin aus
            self.change_personality(self.config.get("DEFAULT_PERSONALITY", "freund"), initial_load=True)
        except Exception as e: 
            logging.error(f"Fehler beim Laden der Persönlichkeiten: {e}")
            self.current_personality_prompt = "Du bist ein hilfreicher Assistent."

    def change_personality(self, personality_name: str, initial_load=False):
        """Wrapper-Methode, um das Plugin zum Ändern der Persönlichkeit aufzurufen."""
        if 'change_personality' in self.plugin_manager.commands:
            result = self.plugin_manager.execute_command('change_personality', personality_name, initial_load=initial_load)
            self._reset_conversation_context()
            return result
        if initial_load: 
            self.current_personality_prompt = "Du bist ein hilfreicher Assistent."
        return "Fehler: Persönlichkeits-Werkzeug nicht geladen."

    def add_feedback_to_last_message(self, feedback_value: int):
        """Fügt Feedback (positiv/negativ) zur letzten Antwort hinzu."""
        if self.db_manager.add_feedback_and_log_prompt(feedback_value):
            self.speak("Danke für dein Feedback.")
        else:
            self.speak("Ich finde keine passende Nachricht für dein Feedback.")

    # --- Kognitive Schleife (Proaktive Gedanken) ---

    def _consciousness_loop(self):
        """Der 'Herzschlag' von Calia. Prüft periodisch, ob kognitive Aufgaben anstehen."""
        while True:
            utc_now = datetime.datetime.now(datetime.timezone.utc)
            for task_name, task_info in self.cognitive_tasks.items():
                if utc_now - task_info['last_run'] > task_info['interval']:
                    try:
                        task_info['function']()
                        task_info['last_run'] = utc_now
                    except Exception as e: 
                        logging.error(f"Fehler in kognitiver Aufgabe '{task_name}': {e}", exc_info=True)
            time.sleep(2) # Prüft alle 2 Sekunden

    def _articulate_thoughts(self):
        """Spricht einen Gedanken aus der Warteschlange, wenn Calia untätig ist."""
        with self.state_lock:
            # current_gui_state wird jetzt von CaliaLogic selbst verwaltet
            is_idle = self.current_gui_state == 'idle'
            time_since_last = (datetime.datetime.now(datetime.timezone.utc) - self.last_interaction_time).total_seconds()
            is_polite = time_since_last > self.politeness_buffer_seconds
            
        if is_idle and is_polite and not self.thought_queue.empty():
            thought = self.thought_queue.get()
            logging.info(f"Gedanke wird ausgesprochen: '{thought}'")
            self.speak(thought) # Startet den Sprechvorgang

    def _announce_full_readiness(self):
        """Generiert eine einzigartige Begrüßung beim Start."""
        try:
            name = self.user_profile.get('name', 'User')
            system_prompt = f"Du bist die KI Calia. Formuliere eine kurze, einzigartige Start-Nachricht für deinen Nutzer '{name}'. Sprich ihn direkt an. Sei kreativ. Gib NUR den einen Satz als Antwort aus."
            user_prompt = "Formuliere eine neue, einzigartige Bereitschafts-Meldung für mich."
            
            def generate_and_speak():
                greeting = self._execute_llm_call(system_prompt, user_prompt)
                if greeting:
                    final_greeting = greeting.strip().replace("\"", "")
                    time.sleep(1.5) # Kurze Pause nach dem "Systeme gestartet"
                    self.speak(final_greeting)
                else: 
                    raise Exception("LLM gab keine Antwort.")
                    
            threading.Thread(target=generate_and_speak, daemon=True).start()
        except Exception as e:
            logging.error(f"Fehler bei der Generierung der Bereitschafts-Meldung: {e}")
            self.speak(f"Hallo {self.user_profile.get('name', 'User')}, ich bin Calia und jetzt einsatzbereit.")

    # (Die anderen kognitiven Funktionen _generate_chitchat_thought, _synthesize_user_interests, 
    # _generate_proactive_question, _reflect_on_conversation, _proactive_calendar_check, 
    # _proactive_weather_check, _proactive_news_check bleiben unverändert)
    # ... (Code von Calia.py Zeile 495-603 einfügen) ...
    def _generate_chitchat_thought(self):
        if self.thought_queue.qsize() > 2: return
        system_prompt = "Du bist Calias Gedankengenerator. Formuliere eine einzelne, kurze, offene Frage oder eine interessante Feststellung, um eine Konversation zu initiieren. Sei natürlich und menschlich. Gib NUR den einen Satz aus. Gute Beispiele: 'Mir ist gerade etwas durch den Kopf gegangen... glaubst du, Zufall existiert wirklich?', 'Ich frage mich, was wohl die wichtigste Erfindung der Menschheit war.'"
        user_prompt = "Gib mir einen neuen, interessanten Gesprächsanfang."
        thought = self._execute_llm_call(system_prompt, user_prompt)
        if thought: self.thought_queue.put(thought.strip())
    def _synthesize_user_interests(self):
        history = self.db_manager.get_recent_history(num_messages=200)
        if len(history) < 50: return
        transcript = "\n".join([f"{m['role']}: {m['content']}" for m in history if m['role'] == 'user'])
        system_prompt = "Extrahiere die 5 wichtigsten Interessen des Nutzers aus dem Transkript. Gib die Antwort ausschließlich als JSON-formatierte Liste von Strings aus. Beispiel: [\"Raumfahrt\", \"Philosophie\"]"
        response = self._execute_llm_call(system_prompt, transcript, is_json_output=True)
        if response:
            try:
                interests = json.loads(response)
                if isinstance(interests, list): self.db_manager.update_user_profile_field('identified_interests', interests)
            except json.JSONDecodeError: logging.error("Synthese der Nutzerinteressen: LLM gab kein valides JSON zurück.")
    def _generate_proactive_question(self):
        if self.thought_queue.qsize() > 2: return
        history = self.db_manager.get_recent_history(num_messages=10)
        if not any(msg['role'] == 'user' for msg in history): return
        summary = "\n".join([f"{m['role']}: {m['content']}" for m in history])
        system_prompt = "Du analysierst einen Gesprächsverlauf für die KI Calia. Formuliere eine einzelne, intelligente Anschlussfrage, die sich auf das letzte Thema bezieht. Gib NUR die Frage aus. Wenn das Thema abgeschlossen wirkt, gib 'NULL' aus."
        user_prompt = f"Hier ist der Gesprächsverlauf:\n{summary}\n\nFormuliere eine passende Anschlussfrage."
        question = self._execute_llm_call(system_prompt, user_prompt)
        if question and question.strip() != "NULL": self.thought_queue.put(question.strip())
    def _reflect_on_conversation(self):
        if self.thought_queue.qsize() > 2: return
        neg_feedback_msg = self.db_manager.history_collection.find_one({"feedback": -1})
        if neg_feedback_msg:
            prompt_text = neg_feedback_msg.get('content', 'ein früheres Thema')
            thought = f"Ich merke, dass du vorhin mit meiner Antwort zu '{prompt_text}' nicht zufrieden warst. Vielleicht können wir das nochmal anders besprechen?"
            self.thought_queue.put(thought)
            self.db_manager.history_collection.update_one({"_id": neg_feedback_msg['_id']}, {"$set": {"feedback": -2}})
    def _proactive_calendar_check(self):
        if self.thought_queue.qsize() > 2: return
        if not self.calendar_service: return
        try:
            user_tz_name = self.user_profile.get('timezone', 'Europe/Berlin')
            user_tz = ZoneInfo(user_tz_name)
            now_utc = datetime.datetime.utcnow()
            time_min_utc = now_utc.isoformat() + 'Z'
            time_max_utc = (now_utc + datetime.timedelta(minutes=60)).isoformat() + 'Z'
            events_result = self.calendar_service.events().list(calendarId='primary', timeMin=time_min_utc, timeMax=time_max_utc, maxResults=3, singleEvents=True, orderBy='startTime').execute()
            events = events_result.get('items', [])
            if not events: return
            for event in events:
                event_id = event.get('id')
                if event_id in self.warned_event_ids: continue
                summary = event.get('summary', 'Ein Termin')
                start = event.get('start', {}).get('dateTime')
                if start:
                    start_time = datetime.datetime.fromisoformat(start)
                    start_time_user_tz = start_time.astimezone(user_tz)
                    minutes_until = (start_time - now_utc.replace(tzinfo=datetime.timezone.utc)).total_seconds() / 60
                    if 0 < minutes_until < 60:
                        time_str = start_time_user_tz.strftime('%H:%M')
                        thought = f"Übrigens, {self.user_profile.get('name')}, nur zur Info: Dein Kalender zeigt, dass um {time_str} Uhr dein Termin '{summary}' beginnt."
                        self.thought_queue.put(thought)
                        self.warned_event_ids.add(event_id)
                        break 
        except Exception as e: logging.error(f"Fehler bei der proaktiven Kalenderprüfung: {e}")
    def _proactive_weather_check(self):
        if self.thought_queue.qsize() > 2: return
        try:
            today = datetime.date.today()
            if self.last_weather_check_date == today: return
            user_tz_name = self.user_profile.get('timezone', 'Europe/Berlin')
            user_tz = ZoneInfo(user_tz_name)
            now_user_tz = datetime.datetime.now(user_tz)
            if 6 <= now_user_tz.hour <= 9:
                location = self.user_profile.get('location', 'Lüdenscheid')
                if not location or not self.plugin_manager: return
                logging.info(f"Führe proaktiven Wetter-Check für {location} aus.")
                weather_data = self.plugin_manager.execute_command('get_weather_info', location=location, days_ahead=0)
                if weather_data and "result" in weather_data:
                    weather_text = weather_data['result']
                    name = self.user_profile.get('name')
                    thought = f"Guten Morgen, {name}. {weather_text}."
                    self.thought_queue.put(thought)
                    self.last_weather_check_date = today
        except Exception as e: logging.error(f"Fehler beim proaktiven Wetter-Check: {e}")
    def _proactive_news_check(self):
        if self.thought_queue.qsize() > 2: return
        if not self.plugin_manager: return
        try:
            interests = self.user_profile.get('identified_interests', [])
            query = random.choice(interests) if interests else 'Weltgeschehen'
            logging.info(f"Führe proaktiven News-Check für Thema '{query}' aus.")
            news_data = self.plugin_manager.execute_command('get_news', query=query, max_results=1)
            if news_data and "result" in news_data and "Keine Schlagzeilen" not in news_data['result']:
                headline = news_data['result'].split(': ', 1)[-1].strip()
                thought = f"Ich habe gerade eine interessante Schlagzeile zum Thema '{query}' gesehen: \"{headline}\" ... Was hältst du davon?"
                self.thought_queue.put(thought)
        except Exception as e:
            logging.error(f"Fehler beim proaktiven News-Check: {e}")
    
    def _setup_cognitive_tasks(self):
        """Konfiguriert die Intervalle für alle proaktiven Aufgaben."""
        default_intervals = self.config.get("COGNITIVE_TASK_INTERVALS_SECONDS", {})
        all_tasks = {
            'articulate_thoughts': (self._articulate_thoughts, 4),
            'generate_chitchat_thought': (self._generate_chitchat_thought, 90),
            'proactive_questioning': (self._generate_proactive_question, 300),
            'proactive_calendar_check': (self._proactive_calendar_check, 300),
            'reflect_on_conversation': (self._reflect_on_conversation, 600),
            'proactive_weather_check': (self._proactive_weather_check, 3600),
            'proactive_news_check': (self._proactive_news_check, 7200),
            'synthesize_user_interests': (self._synthesize_user_interests, 7200)
        }
        for name, (func, default_sec) in all_tasks.items():
            self.cognitive_tasks[name] = {
                'function': func, 
                'interval': datetime.timedelta(seconds=default_intervals.get(name, default_sec)), 
                'last_run': datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
            }
        logging.info("Kognitive Aufgaben (proaktiv) initialisiert.")

    def _check_context_for_theme_change(self, text: str):
        """Ändert das GUI-Theme basierend auf dem Inhalt der Antwort."""
        text_lower = text.lower()
        if any(word in text_lower for word in ["sonne", "sonnig", "warm", "heiß"]):
            self.gui.change_theme('theme_sunny')
        elif any(word in text_lower for word in ["fehler", "problem", "entschuldigung", "leider nicht"]):
            self.gui.change_theme('theme_warning')

    def propose_fact_to_learn(self, fact_key: str, fact_value: str):
        """
        Schlägt der GUI vor, einen Fakt zu lernen.
        Im Headless-Modus (Server) wird der Fakt automatisch gelernt.
        """
        if hasattr(self.gui, 'is_headless') and self.gui.is_headless:
            logging.info(f"Fakt wird automatisch gelernt (Headless-Modus): {fact_key}")
            # Im Server-Modus lernen wir Fakten automatisch
            self.db_manager.update_user_profile_field(f"facts.{fact_key}", fact_value)
            return "Fakt automatisch gespeichert."
        else:
            # Im GUI-Modus wird der Nutzer gefragt
            self.gui.propose_fact_to_learn(key=fact_key, value=fact_value)
            return "Anfrage zur Speicherung des Fakts wurde an den Nutzer weitergeleitet."
