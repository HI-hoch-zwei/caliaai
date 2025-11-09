# -*- coding: utf-8 -*-
# // -- Peter Luebke Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.


import os
import tempfile
import logging
import pygame
from google.cloud import texttospeech
import time
import threading

class TTSManager:
    def __init__(self, tts_client, available_voices: dict):
        """
        Initialisiert den Text-to-Speech Manager.
        :param tts_client: Eine bereits initialisierte Instanz des Google TextToSpeechClient.
        :param available_voices: Ein Dictionary mit den verfügbaren Stimmen.
        """
        self.tts_client = tts_client
        self.available_voices = available_voices
        # Verwende eine Liste, um alte Dateien zu verwalten, falls eine Wiedergabe die andere schnell ablöst
        self.temp_audio_files = []

    def _cleanup_old_files(self):
        """Löscht alle bis auf die letzte temporäre Audiodatei."""
        if not self.temp_audio_files:
            return
        
        files_to_remove = self.temp_audio_files[:-1]
        for file_path in files_to_remove:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError as e:
                logging.warning(f"Konnte alte temporäre Audiodatei nicht löschen: {e}")
        
        self.temp_audio_files = self.temp_audio_files[-1:]


    def synthesize_and_play(self, text: str, voice_key: str, on_done_callback=None):
        """
        Synthetisiert Text zu Sprache und spielt ihn ab.
        Diese Methode ist nun nicht-blockierend.
        :param text: Der Text, der gesprochen werden soll.
        :param voice_key: Der Schlüssel der Stimme aus dem available_voices dict.
        :param on_done_callback: Eine Funktion, die aufgerufen wird, wenn die Wiedergabe beendet ist.
        """
        try:
            # Alte Dateien im Vorfeld bereinigen
            self._cleanup_old_files()

            if not self.tts_client:
                logging.warning("Kein TTS-Client verfügbar, Wiedergabe übersprungen.")
                if on_done_callback:
                    on_done_callback()
                return

            voice_name = self.available_voices.get(voice_key)
            if not voice_name:
                logging.error(f"Stimme '{voice_key}' nicht gefunden. Fallback auf Standard.")
                voice_name = next(iter(self.available_voices.values()), "de-DE-Wavenet-F")

            s_input = texttospeech.SynthesisInput(text=text)
            voice_params = texttospeech.VoiceSelectionParams(language_code="de-DE", name=voice_name)
            audio_conf = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)
            
            response = self.tts_client.synthesize_speech(input=s_input, voice=voice_params, audio_config=audio_conf)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
                temp_audio_file.write(response.audio_content)
                current_audio_file = temp_audio_file.name
                self.temp_audio_files.append(current_audio_file)
            
            # Stoppe jede aktuell laufende Wiedergabe, bevor eine neue gestartet wird.
            pygame.mixer.stop()
            
            sound = pygame.mixer.Sound(current_audio_file)
            sound.play()

            # Starte einen separaten Thread, der wartet und dann die Callback-Funktion aufruft
            threading.Thread(target=self._wait_for_playback_end, args=(on_done_callback,)).start()

        except Exception as e:
            logging.error(f"Kritischer Fehler bei der Sound-Synthese/Wiedergabe: {e}", exc_info=True)
            if on_done_callback:
                on_done_callback()
    
    def _wait_for_playback_end(self, on_done_callback):
        """
        Eine Helfermethode, die in einem eigenen Thread läuft,
        um auf das Ende der Wiedergabe zu warten.
        """
        while pygame.mixer.get_busy():
            time.sleep(0.1)  # Kurze Pause, um die CPU nicht zu belasten
        
        # Wiedergabe ist beendet, rufe die Callback-Funktion auf
        if on_done_callback:
            on_done_callback()