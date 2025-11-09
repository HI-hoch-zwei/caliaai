# -*- coding: utf-8 -*-
# // -- Okami Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.

import logging
import sqlite3
import json

class DeveloperToolsPlugin:
    def __init__(self, logic_controller):
        self.logic = logic_controller

    def register(self):
        return {
            "suggest_new_intents": self.suggest_new_intents
        }

    def suggest_new_intents(self):
        """Analysiert protokollierte, unverstandene Befehle und schlägt neue Intents vor."""
        logging.info("Starte Analyse unverstandener Befehle...")
        try:
            conn = sqlite3.connect(self.logic.db_path)
            cursor = conn.cursor()
            # Hole alle noch nicht analysierten Befehle
            cursor.execute("SELECT id, prompt_text FROM unhandled_prompts WHERE is_analyzed = 0")
            prompts_to_analyze = cursor.fetchall()
            
            if not prompts_to_analyze:
                return "Es gibt keine neuen, unverstandenen Befehle zu analysieren. Gute Arbeit!"

            prompt_texts = [p[1] for p in prompts_to_analyze]
            prompt_ids = [p[0] for p in prompts_to_analyze]
            
            # Spezieller System-Prompt für die KI
            system_prompt = (
                "Du bist ein 'Intent Architect'. Deine Aufgabe ist es, aus der folgenden Liste von Nutzer-Anfragen, "
                "die ein anderer KI-Assistent nicht verstanden hat, neue Intents zu erstellen. "
                "1. Gruppiere semantisch ähnliche Anfragen. "
                "2. Erstelle für jede Gruppe einen prägnanten 'tag'-Namen (z.B. 'get_stock_price'). "
                "3. Formuliere eine Liste von 'patterns', die diese Gruppe abdeckt. "
                "4. Erfinde 2-3 passende 'responses'. "
                "5. Gib deine Vorschläge als valides JSON-Array von Intent-Objekten zurück. Gib NUR das JSON aus, sonst nichts."
            )
            
            # Formatiere die Liste der Befehle für den Prompt
            prompt_list_str = "\n- ".join(prompt_texts)
            full_prompt = f"{system_prompt}\n\n--- Unverstandene Nutzer-Anfragen ---\n- {prompt_list_str}"

            # Sende an die LLM
            response = self.logic.generative_model.generate_content(full_prompt)
            suggested_json = response.text.strip().replace("```json", "").replace("```", "").strip()

            # Markiere die analysierten Prompts in der DB
            cursor.executemany("UPDATE unhandled_prompts SET is_analyzed = 1 WHERE id = ?", [(id,) for id in prompt_ids])
            conn.commit()
            conn.close()

            # Gib die JSON-Vorschläge zurück
            self.logic.gui.set_response(suggested_json) # Zeige das JSON direkt in der GUI
            return "Analyse abgeschlossen. Ich habe einige Vorschläge für neue Intents generiert und zeige sie dir jetzt an."
            
        except Exception as e:
            logging.error(f"Fehler bei der Intent-Vorschlags-Erstellung: {e}", exc_info=True)
            return "Bei der Analyse der Befehle ist ein Fehler aufgetreten."
