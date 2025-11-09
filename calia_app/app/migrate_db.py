# // -- Okami Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.

# -*- coding: utf-8 -*-
import pymongo
import sqlite3
import json
import os

# --- Konfiguration ---
# Stelle sicher, dass diese Namen mit denen in deinem Calia-Code übereinstimmen
MONGO_URL = "mongodb://localhost:27017/"
MONGO_DB_NAME = "calia_intents_db"
INTENTS_COLLECTION = "intents"
SQLITE_DB_NAME = "calia.db"

def migrate_data():
    """Liest Daten aus MongoDB und schreibt sie in eine neue SQLite-Datenbank."""
    
    # Entferne die alte SQLite-DB, falls vorhanden, für einen sauberen Start
    if os.path.exists(SQLITE_DB_NAME):
        os.remove(SQLITE_DB_NAME)
        print(f"Alte '{SQLITE_DB_NAME}' wurde entfernt.")

    # Verbindungen aufbauen
    try:
        mongo_client = pymongo.MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        mongo_db = mongo_client[MONGO_DB_NAME]
        mongo_collection = mongo_db[INTENTS_COLLECTION]
        print("Erfolgreich mit MongoDB verbunden.")
    except Exception as e:
        print(f"Fehler bei der Verbindung mit MongoDB: {e}")
        return

    sqlite_conn = sqlite3.connect(SQLITE_DB_NAME)
    cursor = sqlite_conn.cursor()
    print(f"Neue SQLite-Datenbank '{SQLITE_DB_NAME}' wurde erstellt.")

    # Erstelle die Tabelle in der neuen Datenbank
    cursor.execute('''
        CREATE TABLE intents (
            tag TEXT PRIMARY KEY,
            responses TEXT NOT NULL
        )
    ''')
    print("Tabelle 'intents' in SQLite erstellt.")

    # Lese Daten aus MongoDB und schreibe sie in SQLite
    try:
        count = 0
        for intent_doc in mongo_collection.find({}):
            tag = intent_doc.get('tag')
            responses = intent_doc.get('responses', [])
            
            if tag and responses:
                # SQLite kann keine Listen speichern, also konvertieren wir die Liste in einen JSON-String
                responses_json = json.dumps(responses)
                
                # Füge den Datensatz in die SQLite-Tabelle ein
                cursor.execute("INSERT INTO intents (tag, responses) VALUES (?, ?)", (tag, responses_json))
                count += 1
        
        # Änderungen speichern und Verbindungen schließen
        sqlite_conn.commit()
        print(f"Migration abgeschlossen. {count} Intents wurden erfolgreich übertragen.")

    except Exception as e:
        print(f"Fehler während der Datenübertragung: {e}")
    finally:
        sqlite_conn.close()
        mongo_client.close()

if __name__ == '__main__':
    migrate_data()
