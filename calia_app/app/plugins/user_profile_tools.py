# -*- coding: utf-8 -*-
# // -- Okami Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.

import logging
import sqlite3
import json

class UserProfileToolsPlugin:
    def __init__(self, logic_controller):
        self.logic = logic_controller

    def register(self):
        return {
            "learn_user_fact": self.learn_user_fact,
            "propose_fact_to_learn": self.propose_fact_to_learn
        }

    def learn_user_fact(self, fact_key: str, fact_value: str, is_autonomous: bool = False):
        """
        Speichert einen Fakt über den Nutzer. Wenn autonom aufgerufen, gibt es keine Sprachantwort.
        """
        try:
            current_facts = self.logic.user_profile.get('facts', {})
            
            # Formatiere den Schlüssel konsistent
            formatted_key = fact_key.lower().replace(' ', '_')
            
            # --- START DER ÄNDERUNG ---
            # Prüfe, ob der Fakt bereits bekannt ist, um unnötige Logs/Antworten zu vermeiden
            if current_facts.get(formatted_key) == fact_value:
                logging.info(f"Autonomes Lernen: Fakt '{formatted_key}: {fact_value}' ist bereits bekannt. Überspringe.")
                return "Fakt bereits bekannt." # Stille Rückgabe für die KI

            # Füge den neuen Fakt hinzu oder aktualisiere ihn
            current_facts[formatted_key] = fact_value
            self.logic.user_profile['facts'] = current_facts

            # Speichere die aktualisierten Fakten
            facts_json = json.dumps(current_facts)
            conn = sqlite3.connect(self.logic.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE user_profile SET facts = ? WHERE user_id = 'default'", (facts_json,))
            conn.commit()
            conn.close()
            
            logging.info(f"Neuer Fakt gelernt (Autonom: {is_autonomous}): {formatted_key} = {fact_value}")

            # Gib nur eine Sprachantwort, wenn der Aufruf nicht autonom war
            if not is_autonomous:
                return f"Okay, ich habe mir gemerkt, dass dein(e) {fact_key} {fact_value} ist."
            else:
                # Gib eine stille, aber erfolgreiche Bestätigung für die KI zurück
                return f"Autonomer Fakt '{fact_key}: {fact_value}' erfolgreich gespeichert."
            # --- ENDE DER ÄNDERUNG ---

        except Exception as e:
            logging.error(f"Fehler beim Speichern des Fakts: {e}")
            return "Datenbankfehler beim Speichern des Fakts."
            
    def propose_fact_to_learn(self, fact_key: str, fact_value: str):
        logging.info(f"Schlage vor, Fakt zu lernen: {fact_key} = {fact_value}")
        self.logic.gui.propose_fact_to_learn(fact_key, fact_value)
        return "Die Anfrage zur Speicherung des Fakts wurde an den Nutzer weitergeleitet und wartet auf Bestätigung."

    # NEUE METHODE HINZUFÜGEN
    def set_user_name(self, name: str):
        """Speichert oder ändert den Namen des primären Nutzers."""
        try:
            # Aktualisiere das lokale Profil in CaliaLogic
            self.logic.user_profile['name'] = name

            # Speichere den neuen Namen in der Datenbank
            conn = sqlite3.connect(self.logic.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE user_profile SET name = ? WHERE user_id = 'default'", (name,))
            conn.commit()
            conn.close()
            
            logging.info(f"Benutzername wurde auf '{name}' geändert.")
            return f"Verstanden, ich werde dich von nun an {name} nennen."
        except Exception as e:
            logging.error(f"Fehler beim Ändern des Benutzernamens: {e}")
            return "Datenbankfehler beim Ändern des Namens."