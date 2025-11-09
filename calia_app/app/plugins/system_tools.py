# -*- coding: utf-8 -*-
# // -- Okami Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.

import logging

class SystemToolsPlugin:
    def __init__(self, logic_controller):
        self.logic = logic_controller
        self.config = self.logic.config

    def register(self):
        # Stellen Sie sicher, dass change_personality hier registriert ist
        return {
            "change_voice": self.change_voice,
            "change_personality": self.change_personality,
            "set_llm_engine": self.set_llm_engine
        }
    
    # Die eigentliche Logik bleibt hier im Plugin
    def change_personality(self, personality_name: str, initial_load=False):
        name_lower = personality_name.lower()
        if name_lower in self.logic.personalities:
            self.logic.current_personality_prompt = self.logic.personalities[name_lower]['prompt']
            display_name = self.logic.personalities[name_lower]['name']
            logging.info(f"Persönlichkeit gewechselt zu: {display_name}")
            if not initial_load:
                self.logic.speak(f"In Ordnung. Ich bin jetzt {display_name}.")
            return f"Persönlichkeit erfolgreich zu {display_name} geändert."
        else:
            return f"Ich kenne die Persönlichkeit '{personality_name}' nicht."

    def set_llm_engine(self, engine_name: str):
        engine = engine_name.lower()
        if engine in ['gemini', 'openai']:
            if engine == 'openai' and not self.logic.openai_client:
                return "Die OpenAI-Engine ist nicht verfügbar. Bitte überprüfe deinen API-Schlüssel."
            if engine == 'gemini' and not self.logic.generative_model:
                return "Die Gemini-Engine ist nicht verfügbar. Bitte überprüfe deinen API-Schlüssel."
            
            self.logic.active_llm = engine
            self.logic.openai_history = [] 
            self.logic.speak(f"In Ordnung. Ich verwende jetzt die {engine.capitalize()}-Engine.")
            return f"Engine erfolgreich auf {engine} umgeschaltet."
        else:
            return "Unbekannte Engine. Bitte wähle 'gemini' oder 'openai'."

    def change_voice(self, voice_name: str):
        voice_name_lower = voice_name.lower()
        if voice_name_lower in self.logic.AVAILABLE_VOICES:
            self.logic.current_voice_name = self.logic.AVAILABLE_VOICES[voice_name_lower]
            self.logic.speak(f"Stimme wurde auf {voice_name_lower} geändert.")
            return f"Stimme erfolgreich geändert."
        else:
            return "Diese Stimme kenne ich nicht. Verfügbar sind: " + ", ".join(self.logic.AVAILABLE_VOICES.keys())
