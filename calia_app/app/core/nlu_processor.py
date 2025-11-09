# -*- coding: utf-8 -*-
# // -- Peter Luebke Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.


import json
import pickle
import numpy as np
import nltk
import logging

# WICHTIGE ÄNDERUNG: Wir importieren TensorFlow/Keras nicht mehr hier oben!
# from tensorflow.keras.models import load_model

class NLUProcessor:
    def __init__(self, intents_file, model_file, words_file, classes_file):
        logging.info("Initialisiere NLU-Prozessor (verzögertes Laden)...")
        try:
            with open(intents_file, 'r', encoding='utf-8') as file:
                self.intents = json.load(file)
            
            with open(words_file, 'rb') as file:
                self.words = pickle.load(file)
            
            with open(classes_file, 'rb') as file:
                self.classes = pickle.load(file)

            # NEU: Wir speichern nur den Pfad zum Modell und laden es noch nicht.
            self.model_file = model_file
            self.model = None # Das Modell ist anfangs leer.
            
            logging.info("NLU-Prozessor-Daten geladen. Modell wird bei erster Nutzung geladen.")
        except FileNotFoundError as e:
            logging.critical(f"Eine Modelldatei wurde nicht gefunden: {e}")
            raise e
        except Exception as e:
            logging.error(f"Fehler bei der Initialisierung des NLU-Prozessors: {e}")
            raise e

    # NEUE METHODE: Diese Methode lädt das Modell, aber nur wenn es noch nicht geladen ist.
    def _load_model_if_needed(self):
        if self.model is None:
            try:
                logging.info("Lade TensorFlow-Modell jetzt... (einmalige Verzögerung)")
                # Der Import passiert erst hier, sicher und isoliert.
                from tensorflow.keras.models import load_model
                self.model = load_model(self.model_file)
                logging.info("TensorFlow-Modell erfolgreich geladen.")
            except Exception as e:
                logging.critical(f"Konnte das TensorFlow-Modell nicht laden: {e}")
                # Wir setzen das Modell auf ein Dummy-Objekt, um weitere Fehler zu vermeiden.
                class DummyModel:
                    def predict(self, *args, **kwargs): return np.array([[0.0]])
                self.model = DummyModel()
                raise e

    def _clean_up_sentence(self, sentence):
        sentence_words = nltk.word_tokenize(sentence)
        lemmatizer = nltk.stem.WordNetLemmatizer()
        sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
        return sentence_words

    def _bag_of_words(self, sentence):
        sentence_words = self._clean_up_sentence(sentence)
        bag = [0] * len(self.words)
        for s_word in sentence_words:
            for i, word in enumerate(self.words):
                if word == s_word:
                    bag[i] = 1
        return np.array(bag)

    def predict_intent(self, sentence):
        if not sentence:
            return None

        try:
            # NEUER AUFRUF: Stelle sicher, dass das Modell geladen ist, bevor wir es benutzen.
            self._load_model_if_needed()

            bow = self._bag_of_words(sentence)
            res = self.model.predict(np.array([bow]), verbose=0)[0]
            
            ERROR_THRESHOLD = 0.25
            results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
            
            results.sort(key=lambda x: x[1], reverse=True)
            
            if not results:
                return None

            return_list = []
            for r in results:
                return_list.append({"intent": self.classes[r[0]], "probability": str(r[1])})
            
            return return_list
        except Exception as e:
            logging.error(f"Fehler bei der Intent-Vorhersage: {e}")
            return None

    def get_response(self, intent_tag):
        if not intent_tag:
            return "Ich bin mir nicht sicher, wie ich darauf antworten soll."

        for intent in self.intents['intents']:
            if intent['tag'] == intent_tag:
                return np.random.choice(intent['responses'])
        
        return "Entschuldigung, das habe ich nicht verstanden."