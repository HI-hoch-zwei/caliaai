import pymongo

MONGO_CLIENT_URL = "mongodb://localhost:27017/"
DB_NAME = "calia_intents_db"
COLLECTION_NAME = "intents"

try:
    client = pymongo.MongoClient(MONGO_CLIENT_URL)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    # Zaehle die Anzahl der Dokumente
    num_documents = collection.count_documents({})
    print(f"Anzahl der Dokumente (Intents) in der Collection: {num_documents}")

    # Zaehle die Gesamtanzahl der Patterns und Responses
    total_patterns = 0
    total_responses = 0

    # Iteriere ueber alle Intents und summiere die Laengen der Listen
    for doc in collection.find({}, {'patterns': 1, 'responses': 1}):
        total_patterns += len(doc.get('patterns', []))
        total_responses += len(doc.get('responses', []))

    print(f"Gesamtanzahl der Patterns in der Datenbank: {total_patterns}")
    print(f"Gesamtanzahl der Responses in der Datenbank: {total_responses}")
    print(f"Gesamtzahl der Lerndaten (Patterns + Responses): {total_patterns + total_responses}")

except pymongo.errors.ConnectionFailure as e:
    print(f"Fehler: Verbindung zu MongoDB fehlgeschlagen: {e}")
except Exception as e:
    print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
finally:
    if 'client' in locals() and client:
        client.close()