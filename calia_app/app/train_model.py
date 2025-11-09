# -*- coding: utf-8 -*-
# // -- Peter Luebke Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.


# -*- coding: utf-8 -*-
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import Adam
import nltk
from nltk.stem import WordNetLemmatizer
import pickle
import os
import sys
import datetime
import pymongo # Fuer MongoDB
import scipy.sparse # Fuer speichereffiziente Sparse Matrices
from db_config import MONGO_CLIENT_URL, DB_NAME, COLLECTION_NAME

# Funktion, um die Ausgabe sowohl auf die Konsole als auch in eine Datei zu schreiben
class DualOutput:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, 'a', encoding='utf-8')
        sys.stdout = self

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

    def close(self):
        sys.stdout = self.terminal
        self.log.close()

print("Starte das Training fuer das KI-Modell C.A.L.I.A....")
print("---------------------------------------")

# MongoDB Konfiguration
# MONGO_CLIENT_URL = "mongodb://localhost:27017/"
# DB_NAME = "calia_intents_db"
# COLLECTION_NAME = "intents"

timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
script_dir = os.path.dirname(__file__)
log_filename = os.path.join(script_dir, f"training_log_{timestamp}.txt")

original_stdout = sys.stdout
sys.stdout = DualOutput(log_filename)

print(f"--- TRAININGSDOKUMENTATION FUER CALIA ---")
print(f"Startzeit des Trainings: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Skriptpfad: {script_dir}\n")

try:
    print("Stelle sicher, dass die NLTK-Daten 'punkt' und 'wordnet' vorhanden sind...")
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('wordnet', quiet=True)
        print("NLTK-Daten sind bereit.")
    except Exception as e:
        print(f"FEHLER: NLTK-Daten konnten nicht heruntergeladen werden: {e}")
        print("Bitte ueberpruefe deine Internetverbindung oder fuehre 'python -m nltk.downloader punkt wordnet' manuell aus.")
        sys.exit(1)

    lemmatizer = WordNetLemmatizer()

    words = []
    classes = []
    documents = [] # Format: (word_list, tag)
    ignore_letters = ['?', '!', '.', ',']

    # --- DATEN AUS MONGODB LADEN ---
    print(f"Verbinde zu MongoDB und lade Intents aus '{DB_NAME}'...")
    try:
        client = pymongo.MongoClient(MONGO_CLIENT_URL)
        client.admin.command('ping') # Teste die Verbindung
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
    except pymongo.errors.ConnectionFailure as e:
        raise ConnectionError(f"Verbindung zu MongoDB fehlgeschlagen: {e}. Ist der Server gestartet?")
    
    # Lade alle Intent-Dokumente
    mongo_intents = collection.find({})
    
    num_patterns_loaded = 0
    num_responses_loaded = 0 # Nur zum Zaehlen, nicht fuer Training
    
    # Sammle alle Patterns und Responses in Listen zur spaeteren Verarbeitung
    all_pattern_lists = []
    all_tags = []

    for intent_doc in mongo_intents:
        tag = intent_doc.get('tag')
        patterns = intent_doc.get('patterns', [])
        responses = intent_doc.get('responses', [])
        
        if tag and tag not in classes: # Fuege Tag zur Klasse hinzu, wenn noch nicht vorhanden
            classes.append(tag)

        for pattern_text in patterns:
            word_list = nltk.word_tokenize(pattern_text)
            words.extend(word_list) # Sammle alle Woerter fuer das Vokabular
            all_pattern_lists.append(word_list) # Speichere die tokenisierte Pattern-Liste
            all_tags.append(tag) # Speichere den zugehoerigen Tag
            num_patterns_loaded += 1
            
        num_responses_loaded += len(responses) # Zaehle Responses nur zu Informationszwecken
    
    client.close() # Verbindung schliessen
    
    if not all_pattern_lists:
        raise ValueError("Keine Trainingsmuster aus MongoDB geladen. Ist die Datenbank leer oder falsch befuellt?")
    
    print(f"Intents und Patterns erfolgreich aus MongoDB geladen.")
    print(f"Anzahl der geladenen Patterns: {num_patterns_loaded}")
    print(f"Anzahl der geladenen Responses: {num_responses_loaded}")
    print(f"Gesamtzahl der Lerndaten (Patterns + Responses): {num_patterns_loaded + num_responses_loaded}\n")

    # --- WEITERE VERARBEITUNG DER DATEN ---
    # Erstelle das Vokabular (words)
    words = [lemmatizer.lemmatize(word.lower()) for word in words if word not in ignore_letters]
    words = sorted(list(set(words)))
    classes = sorted(list(set(classes))) # Sicherstellen, dass Klassen sortiert und einzigartig sind

    # Speichere Woerter und Klassen fuer die spaetere Nutzung durch Calia
    with open(os.path.join(script_dir, 'words.pkl'), 'wb') as f:
        pickle.dump(words, f)
    with open(os.path.join(script_dir, 'classes.pkl'), 'wb') as f:
        pickle.dump(classes, f)
    print("Woerter und Klassen erfolgreich gespeichert ('words.pkl', 'classes.pkl').")

    print("Erstelle numerische Trainingsdaten (Bag of Words als Sparse Matrix)...")
    
    train_x_bags = []
    train_y_one_hot = []
    
    # Erstelle die Bag-of-Words-Vektoren und One-Hot-Encoded Labels
    for i, pattern_word_list in enumerate(all_pattern_lists):
        bag = [0] * len(words)
        lemmatized_pattern_words = [lemmatizer.lemmatize(word.lower()) for word in pattern_word_list]
        
        for j, word_in_vocab in enumerate(words):
            if word_in_vocab in lemmatized_pattern_words:
                bag[j] = 1 # Setze 1, wenn Wort im Pattern ist

        # Erstelle das One-Hot-Encoded Label
        output_row = [0] * len(classes)
        try:
            output_row[classes.index(all_tags[i])] = 1
        except ValueError: # Falls ein Tag in der DB ist, der nicht in classes gelandet ist (unwahrscheinlich)
            print(f"Warnung: Tag '{all_tags[i]}' nicht in der Klassenliste gefunden. Ueberspringe Muster.")
            continue

        train_x_bags.append(bag)
        train_y_one_hot.append(output_row)

    # Konvertiere Bag-of-Words-Listen in eine effiziente Sparse Matrix
    # Verwende np.int8, da Werte nur 0 oder 1 sind, um noch mehr Speicher zu sparen
    train_x = scipy.sparse.csr_matrix(train_x_bags, dtype=np.int8) 
    train_y = np.array(train_y_one_hot, dtype=np.int8)

    if train_x.shape[0] == 0 or train_x.shape[1] == 0 or train_y.shape[0] == 0:
        raise ValueError("Nicht genuegend Trainingsdaten nach Bag-of-Words-Verarbeitung gefunden. Pruefe die geladenen Daten und das Vokabular.")

    print(f"Trainingsdaten vorbereitet: {train_x.shape[0]} Muster fuer {len(classes)} Klassen.")
    print(f"Bag-of-Words-Matrix-Groesse: {train_x.shape}, Datentyp: {train_x.dtype}, Sparse-Format: {type(train_x)}")
    # Speicherverbrauch der Sparse Matrix koennte hier geschaetzt werden, ist aber komplexer als bei dichten Arrays

    print("Erstelle das neuronale Keras-Modell...")
    model = Sequential()
    # Input-Shape ist die Laenge des Bag-of-Words-Vektors (Anzahl der einzigartigen Woerter)
    model.add(Dense(128, input_shape=(train_x.shape[1],), activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(64, activation='relu'))
    model.add(Dropout(0.5))
    # Output-Schicht: Anzahl der Neuronen = Anzahl der Klassen (Intents), Softmax fuer Wahrscheinlichkeiten
    model.add(Dense(train_y.shape[1], activation='softmax')) # train_y.shape[1] ist die Anzahl der Klassen

    optimizer = Adam(learning_rate=0.001)
    model.compile(loss='categorical_crossentropy', optimizer=optimizer, metrics=['accuracy'])

    print(f"\nModell-Hyperparameter:")
    print(f"  Input-Shape: {train_x.shape[1]}")
    print(f"  Schichten: Dense(128, relu) -> Dropout(0.5) -> Dense(64, relu) -> Dropout(0.5) -> Dense({train_y.shape[1]}, softmax)")
    print(f"  Optimierer: Adam (Lernrate={optimizer.learning_rate.numpy():.4f})")
    print(f"  Loss-Funktion: Categorical Crossentropy")
    print(f"  Metriken: Accuracy")
    print(f"  Epochen: 300")
    print(f"  Batch-Groesse: 5\n")

    print("Starte das Modelltraining...")
    # Keras/TensorFlow koennen scipy.sparse.csr_matrix direkt als Input verarbeiten
    hist = model.fit(train_x, train_y, epochs=1000, batch_size=5, verbose=1)

    model.save(os.path.join(script_dir, 'calia_model.keras'))
    print("\nTraining abgeschlossen. Modell wurde als 'calia_model.keras' gespeichert.")
    print(f"Trainingsverlauf:\n{hist.history}")

except ConnectionError as ce:
    print(f"\nFEHLER: Datenbankverbindungsproblem: {ce}")
    print("Bitte stellen Sie sicher, dass Ihr MongoDB-Server laeuft und unter der angegebenen URL erreichbar ist.")
except FileNotFoundError as e:
    print(f"\nFEHLER: Datei nicht gefunden: {e}")
    print("Bitte stellen Sie sicher, dass alle benoetigten Dateien im richtigen Verzeichnis liegen.")
except json.JSONDecodeError:
    print("\nFEHLER: Ungueltiges JSON-Format. Bitte ueberpruefen Sie 'initial_intents.json'.")
except ValueError as ve:
    print(f"\nFEHLER: Datenproblem bei der Verarbeitung: {ve}")
    print("Moeglicherweise ist Ihre Datenbank leer oder die Datenstruktur ist unerwartet.")
except pymongo.errors.PyMongoError as e:
    print(f"\nFEHLER: MongoDB-Operation fehlgeschlagen: {e}")
    print("Ueberpruefen Sie Ihre MongoDB-Konfiguration und die Server-Logs.")
except Exception as e:
    print(f"\nEin unerwarteter Fehler ist aufgetreten: {e}")
    import traceback
    traceback.print_exc() # Gibt den kompletten Traceback aus
    print("Bitte ueberpruefen Sie die Fehlermeldung fuer weitere Details.")

finally:
    print(f"\nEndzeit des Trainings: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Trainingsdokumentation gespeichert in: {log_filename}")
    print("---------------------------------------")
    
    if isinstance(sys.stdout, DualOutput):
        sys.stdout.close()
        sys.stdout = original_stdout

    print("\nDas Programm ist beendet. Druecke eine beliebige Taste, um das Fenster zu schliessen...")
    if sys.stdin.isatty():
        input()
    else:
        pass