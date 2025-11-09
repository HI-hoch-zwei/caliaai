# -*- coding: utf-8 -*-
# // -- Okami Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.

import logging
import chromadb
import uuid
import google.generativeai as genai
from chromadb.config import Settings

class MemoryManagerPlugin:
    def __init__(self, logic_controller):
        self.logic = logic_controller
        self.embedding_model = 'models/text-embedding-004'
        
        try:
            # --- START KORREKTUR ---
            # Wir verwenden PersistentClient und übergeben explizit die Einstellung zum Deaktivieren der Telemetrie.
            self.chroma_client = chromadb.PersistentClient(
                path="calia_memory",
                settings=Settings(anonymized_telemetry=False)
            )
            # --- ENDE KORREKTUR ---

            self.collection = self.chroma_client.get_or_create_collection(name="conversations")
            logging.info("ChromaDB Memory-Manager erfolgreich initialisiert.")
        except Exception as e:
            logging.error(f"Fehler bei der Initialisierung von ChromaDB: {e}", exc_info=True)
            self.collection = None

    def register(self):
        return {}

    def add_memory(self, conversation_turn: str):
        """Wandelt einen Gesprächsabschnitt in einen Vektor um und speichert ihn."""
        if not self.collection: return
        try:
            embedding = genai.embed_content(
                model=self.embedding_model,
                content=conversation_turn,
                task_type="retrieval_document"
            )
            memory_id = str(uuid.uuid4())
            
            self.collection.add(
                embeddings=[embedding['embedding']],
                documents=[conversation_turn],
                ids=[memory_id]
            )
            
            # --- KORREKTUR: Diese Zeile wird entfernt, da PersistentClient automatisch speichert. ---
            # self.chroma_client.persist() 
            
            logging.info(f"Neue Erinnerung '{memory_id}' zum Langzeitgedächtnis hinzugefügt.")
        except Exception as e:
            logging.error(f"Fehler beim Hinzufügen einer Erinnerung: {e}", exc_info=True)

    def retrieve_memories(self, query: str, n_results: int = 3) -> str:
        # Diese Methode bleibt unverändert.
        if not self.collection or self.collection.count() == 0:
            return "Keine relevanten Langzeit-Erinnerungen gefunden."
        try:
            query_embedding = genai.embed_content(
                model=self.embedding_model,
                content=query,
                task_type="retrieval_query"
            )
            results = self.collection.query(
                query_embeddings=[query_embedding['embedding']],
                n_results=n_results
            )
            if not results or not results['documents'][0]:
                return "Keine relevanten Langzeit-Erinnerungen gefunden."
            
            retrieved_docs = results['documents'][0]
            formatted_memories = "\n\n".join([f"--- Erinnerung ---\n{doc}\n--- Ende Erinnerung ---" for doc in retrieved_docs])
            logging.info(f"{len(retrieved_docs)} relevante Erinnerungen gefunden.")
            return formatted_memories
        except Exception as e:
            logging.error(f"Fehler beim Abrufen von Erinnerungen: {e}", exc_info=True)
            return "Fehler beim Zugriff auf das Langzeitgedächtnis."