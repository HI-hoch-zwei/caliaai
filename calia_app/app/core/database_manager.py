# -*- coding: utf-8 -*-
# // -- Peter Luebke Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.


import pymongo
import json
import logging
from datetime import datetime, timedelta

class DatabaseManager:
    def __init__(self, db_path: str = None):
        """
        Initialisiert den DatabaseManager für MongoDB.
        """
        self.client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.db = self.client["calia_db"]
        self.history_collection = self.db["conversation_history"]
        self.profile_collection = self.db["user_profile"]
        self.unhandled_prompts_collection = self.db["unhandled_prompts"]
        
        self.init_database()

    def _get_connection(self):
        return self.client

    def init_database(self):
        """Stellt sicher, dass Indizes für schnellen Zugriff existieren."""
        try:
            self.client.admin.command('ping')
            self.history_collection.create_index([("timestamp", pymongo.DESCENDING)])
            self.profile_collection.create_index([("user_id", pymongo.ASCENDING)], unique=True)
            logging.info(f"Datenbank-Manager für MongoDB initialisiert und Indizes sichergestellt.")
        except pymongo.errors.ConnectionFailure as e:
            logging.error(f"Schwerer Fehler bei der MongoDB-Verbindung: {e}", exc_info=True)
            raise e

    def add_to_history(self, role: str, content: str):
        """Fügt eine neue Nachricht zur Konversations-Sammlung hinzu."""
        try:
            document = {
                "timestamp": datetime.now(),
                "role": role,
                "content": content,
                "feedback": 0
            }
            self.history_collection.insert_one(document)
        except Exception as e:
            logging.error(f"Fehler beim Speichern der Konversations-Historie: {e}")

    def get_recent_history(self, num_messages: int = 10) -> list:
        """Holt die letzten 'n' Nachrichten aus der Datenbank."""
        try:
            cursor = self.history_collection.find({}, {"_id": 0, "role": 1, "content": 1})\
                                            .sort("timestamp", pymongo.DESCENDING)\
                                            .limit(num_messages)
            history = list(cursor)
            return list(reversed(history))
        except Exception as e:
            logging.error(f"Fehler beim Laden der Konversations-Historie: {e}")
            return []

    def load_user_profile(self) -> dict:
        """Lädt das Benutzerprofil 'default' aus der Datenbank."""
        try:
            profile = self.profile_collection.find_one({"user_id": "default"})
            if profile:
                profile.pop('_id', None)
                return profile
            else:
                default_profile = {
                    "user_id": "default", 
                    "name": "mein Freund", 
                    "location": "Lüdenscheid", 
                    "facts": {}, 
                    "style_profile_cache": None, 
                    "timezone": "Europe/Berlin",
                    "identified_interests": []
                }
                self.profile_collection.insert_one(default_profile.copy())
                default_profile.pop('_id', None)
                return default_profile
        except Exception as e:
            logging.error(f"Fehler beim Laden des Benutzerprofils: {e}")
            return {"user_id": "default", "name": "Error", "facts": {}, "timezone": "UTC", "identified_interests": []}

    def update_user_profile_field(self, field_name: str, value: any):
        """Aktualisiert ein einzelnes Feld im Benutzerprofil."""
        try:
            self.profile_collection.update_one(
                {"user_id": "default"},
                {"$set": {field_name: value}},
                upsert=True
            )
            logging.info(f"Benutzerprofil-Feld '{field_name}' aktualisiert.")
        except Exception as e:
            logging.error(f"Fehler beim Aktualisieren des Profils: {e}")

    def add_feedback_and_log_prompt(self, feedback_value: int):
        """Fügt Feedback hinzu und protokolliert bei Bedarf den missverstandenen Befehl."""
        try:
            last_assistant_msg = self.history_collection.find_one(
                {"role": "assistant"},
                sort=[("timestamp", pymongo.DESCENDING)]
            )
            if not last_assistant_msg:
                logging.warning("Feedback konnte nicht hinzugefügt werden: Keine Assistenten-Nachricht gefunden.")
                return False

            last_id = last_assistant_msg['_id']
            self.history_collection.update_one(
                {"_id": last_id},
                {"$set": {"feedback": feedback_value}}
            )

            if feedback_value == -1:
                user_prompt_entry = self.history_collection.find_one(
                    {"role": "user", "timestamp": {"$lt": last_assistant_msg["timestamp"]}},
                    sort=[("timestamp", pymongo.DESCENDING)]
                )
                if user_prompt_entry:
                    prompt_to_log = user_prompt_entry['content']
                    self.unhandled_prompts_collection.insert_one({
                        "prompt_text": prompt_to_log,
                        "timestamp": datetime.now(),
                        "is_analyzed": False
                    })
                    logging.info(f"Negatives Feedback erhalten. Missverstandener Befehl '{prompt_to_log}' protokolliert.")
            
            logging.info(f"Feedback ({feedback_value}) zu Nachricht ID {last_id} hinzugefügt.")
            return True
        except Exception as e:
            logging.error(f"Fehler beim Hinzufügen von Feedback: {e}")
            return False

    def get_unhandled_prompt(self):
        """Holt einen einzelnen, noch nicht analysierten Prompt aus der DB."""
        try:
            return self.unhandled_prompts_collection.find_one({"is_analyzed": False})
        except Exception as e:
            logging.error(f"Fehler beim Abrufen eines unhandled_prompt: {e}")
            return None

    def mark_prompt_as_analyzed(self, document_id):
        """Markiert einen Prompt in der DB als analysiert."""
        try:
            self.unhandled_prompts_collection.update_one(
                {"_id": document_id},
                {"$set": {"is_analyzed": True}}
            )
        except Exception as e:
            logging.error(f"Fehler beim Markieren eines Prompts als analysiert: {e}")
            
    def get_history_around_timestamp(self, timestamp: datetime, num_messages: int = 5) -> list:
        """Holt Nachrichten vor und nach einem bestimmten Zeitpunkt für Kontext."""
        try:
            half_messages = num_messages // 2
            
            before_cursor = self.history_collection.find({"timestamp": {"$lt": timestamp}})\
                                                   .sort("timestamp", pymongo.DESCENDING)\
                                                   .limit(half_messages)
            
            after_cursor = self.history_collection.find({"timestamp": {"$gte": timestamp}})\
                                                  .sort("timestamp", pymongo.ASCENDING)\
                                                  .limit(half_messages + 1)

            history_docs = sorted(list(before_cursor) + list(after_cursor), key=lambda x: x['timestamp'])
            
            for doc in history_docs:
                doc['_id'] = str(doc['_id'])
                
            return history_docs
        except Exception as e:
            logging.error(f"Fehler beim Laden der Kontext-Historie: {e}")
            return []