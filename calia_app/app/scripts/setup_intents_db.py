# -*- coding: utf-8 -*-
import sqlite3 # Behalten, falls du es doch noch brauchst, aber nicht mehr direkt genutzt
import pymongo
import json
import os
import random
import datetime
import sys

# --- Konfiguration ---
MONGO_CLIENT_URL = "mongodb://localhost:27017/" # Standard-MongoDB-URL
DB_NAME = "calia_intents_db"
COLLECTION_NAME = "intents" # Eine Collection fuer alle Intents
INITIAL_INTENTS_FILE = 'initial_intents.json'

def get_mongo_collection():
    """Stellt Verbindung zu MongoDB her und gibt die Collection zurueck."""
    try:
        client = pymongo.MongoClient(MONGO_CLIENT_URL)
        # Der Ping-Befehl ist eine gute Moeglichkeit, die Verbindung zu testen.
        # Er wird scheitern, wenn der Server nicht erreichbar ist.
        client.admin.command('ping') 
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        print(f"Verbindung zu MongoDB erfolgreich hergestellt: Datenbank '{DB_NAME}', Collection '{COLLECTION_NAME}'.")
        return collection
    except pymongo.errors.ConnectionFailure as e:
        print(f"FEHLER: Verbindung zu MongoDB fehlgeschlagen: {e}")
        print("Bitte stellen Sie sicher, dass der MongoDB-Server laeuft (Standard-Port 27017).")
        sys.exit(1) # Beende das Skript bei Verbindungsfehler
    except Exception as e:
        print(f"Ein unerwarteter Fehler bei der MongoDB-Verbindung ist aufgetreten: {e}")
        sys.exit(1)

def populate_db_from_json(collection, json_file_path):
    """Fuellt die Datenbank mit Daten aus einer JSON-Datei."""
    print(f"Lade initiale Intents von '{json_file_path}'...")
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, dict) or 'intents' not in data:
            raise ValueError("Die JSON-Datei hat nicht das erwartete Format. Sie muss ein Objekt mit dem Schluessel 'intents' sein.")

        intents_to_insert = []
        for intent_data in data['intents']:
            # In MongoDB speichern wir den gesamten Intent als ein Dokument
            intents_to_insert.append(intent_data)
            
        if intents_to_insert:
            collection.insert_many(intents_to_insert)
            print(f"Initiale Intents von '{json_file_path}' in MongoDB geladen.")
        else:
            print(f"Keine initialen Intents in '{json_file_path}' gefunden.")
        return True
    except FileNotFoundError:
        print(f"Fehler: '{json_file_path}' nicht gefunden. Initialisiere mit minimalen Daten.")
        return False
    except json.JSONDecodeError:
        print(f"Fehler: '{json_file_path}' ist keine gueltige JSON-Datei.")
        print("Bitte ueberpruefe die Syntax (fehlende Kommas, Klammern, Anfuehrungszeichen).")
        return False
    except ValueError as ve:
        print(f"Fehler bei der JSON-Struktur: {ve}")
        return False
    except pymongo.errors.PyMongoError as e:
        print(f"Fehler beim Einfuegen in MongoDB: {e}")
        return False
    except Exception as e:
        print(f"Ein Fehler ist beim Laden der JSON-Datei aufgetreten: {e}")
        return False
    return True

def generate_extensive_intents(collection):
    """Generiert eine sehr grosse Menge an zusaetzlichen Intents und speichert sie in der DB."""
    print("\nGeneriere zusaetzliche, umfangreiche Intents...")
    
    # NEUE UND MASSIV ERWEITERTE THEMENGAMMA
    topics_data = {
        "politik": {
            "description": "Fragen zur Politik und Regierungsfuehrung.",
            "sub_topics": {
                "aktuelle_ereignisse": {
                    "patterns": ["Was sind die neuesten politischen Nachrichten?", "Gibt es Neuigkeiten aus der Regierung?", "Was ist das aktuelle Thema in der Weltpolitik?", "Aktuelle politische Lage?", "Neueste Entwicklungen in der Politik?", "Was tut die Regierung gerade?", "Politischer Tagesbericht.", "Internationale politische Lage.", "Was gibt es Neues in der Politik von {Land}?", "Neueste Infos zur Politik."],
                    "responses": ["Ich recherchiere die neuesten politischen Nachrichten fuer dich.", "Die aktuellen politischen Ereignisse sind komplex. Einen Moment, ich fasse sie zusammen.", "Gerne, hier ist eine Zusammenfassung der politischen Lage.", "Die neuesten Entwicklungen sind wie folgt: [Details].", "Es gibt keine bedeutenden neuen politischen Nachrichten zur Zeit."]
                },
                "wahlen": {
                    "patterns": ["Wer kandidiert bei der naechsten Wahl?", "Wie funktioniert das Wahlsystem in Deutschland?", "Wann sind die naechsten Wahlen?", "Ergebnisse der letzten Wahl?", "Wahlprognosen?", "Parteien fuer die Bundestagswahl?", "Was muss ich zur Wahl wissen?", "Ueberblick ueber das Wahlsystem.", "Welche Parteien stehen zur Wahl in {Land}?", "Informationen zur Wahl in {Stadt}?"],
                    "responses": ["Ich kann dir Informationen zu den naechsten Wahlen und Kandidaten geben.", "Das Wahlsystem ist so aufgebaut: [Erklaerung].", "Die Wahlergebnisse waren wie folgt: [Ergebnisse].", "Zur naechsten Wahl kandidieren: [Kandidatenliste]."]
                },
                "internationale_beziehungen": {
                    "patterns": ["Was ist die NATO?", "Erklaere die Beziehung zwischen {Land1} und {Land2}.", "Welche Rolle spielt die UN?", "Internationale Konflikte?", "Diplomatische Beziehungen zwischen {Land1} und {Land2}?", "Was ist der Weltsicherheitsrat?", "Gibt es Spannungen zwischen {Land1} und {Land2}?", "Was sind die Ziele der WTO?", "Ueber die EU?"],
                    "responses": ["Internationale Beziehungen sind ein weites Feld. Hier sind einige Fakten.", "Die Rolle der UN ist es, den Weltfrieden zu sichern.", "Die NATO ist ein militaerisches Buendnis.", "Die Beziehungen zwischen {Land1} und {Land2} sind [Beschreibung]."]
                },
                "gesetze": {
                    "patterns": ["Was ist das BGB?", "Erklaere ein neues Gesetz.", "Wie entsteht ein Gesetz?", "Bedeutung von {Gesetz}?", "Gesetzesaenderungen in {Bereich}?", "Rechtslage zu {Thema}?", "Was besagt das {Gesetz}?", "Gibt es neue Regelungen zu {Thema}?", "Kannst du mir {Gesetz} erklaeren?", "Ueber das deutsche Rechtssystem."],
                    "responses": ["Ein Gesetz entsteht durch [Prozess].", "Das BGB regelt das Zivilrecht in Deutschland.", "{Gesetz} bedeutet [Erklaerung].", "Die neue Regelung besagt, dass [Regelung]."]
                },
                "buergerrechte": {
                    "patterns": ["Was sind meine Rechte?", "Wie kann ich mein Wahlrecht ausueben?", "Grundrechte in Deutschland?", "Datenschutzrechte?", "Recht auf Meinungsfreiheit?", "Was ist Versammlungsfreiheit?", "Meine Rechte als Buerger in {Land}?", "Informiere mich ueber Buergerrechte."],
                    "responses": ["Deine Buergerrechte umfassen [Rechte].", "Das Wahlrecht kann durch [Prozess] ausgeuebt werden.", "Grundrechte schuetzen dich vor staatlicher Willkuer.", "Das Recht auf Meinungsfreiheit ist [Erklaerung]."]
                },
                "fragen_zu_parteien": {
                    "patterns": ["Was sind die Ziele der {Partei}?", "Wer fuehrt die {Partei} an?", "Geschichte der {Partei}?", "Ideologie der {Partei}?", "Programmpunkte der {Partei}?", "Was vertritt die {Partei}?", "Ueberblick ueber {Partei}.", "Standpunkte der {Partei} zu {Thema}?"],
                    "responses": ["Die {Partei} hat folgende Ziele: [Ziele].", "Der Vorsitzende der {Partei} ist [Name].", "Die {Partei} vertritt die Ideologie [Ideologie].", "Die wichtigsten Programmpunkte sind [Punkte]."]
                },
                "politiker_biografien": {
                    "patterns": ["Wer ist {Politikername}?", "Erzaehl mir etwas ueber {Politikername}.", "Lebenslauf von {Politikername}?", "Wichtige Entscheidungen von {Politikername}?", "Biografie von {Politikername}.", "Ueber {Politikername}.", "Was hat {Politikername} erreicht?", "Wer ist der aktuelle {Titel} in {Land}?"],
                    "responses": ["{Politikername} ist [Beschreibung].", "Hier sind einige Fakten aus dem Leben von {Politikername}.", "Die wichtigsten Stationen im Leben von {Politikername} sind [Stationen].", "{Politikername} ist bekannt fuer [Leistung]."]
                }
            }
        },
        "humor": {
            "description": "Witze und lustige Fakten.",
            "sub_topics": {
                "tierwitze": {
                    "patterns": ["Erzaehl mir einen Tierwitz.", "Hast du einen lustigen Tierwitz?", "Einen Witz ueber Tiere bitte.", "Witz mit Tieren.", "Tierischer Witz.", "Noch ein Tierwitz."],
                    "responses": ["Was ist gruen und rennt durch den Garten? Ein Rasen-Stier!", "Warum hat der Hund seinen Schwanz gewedelt? Weil der Schwanz den Hund nicht wedeln kann!", "Was macht ein Gluehwuermchen, wenn es wuetend ist? Es platzt vor Wut!", "Was ist eine Giraffe, die einen Elefanten isst? Eine sehr hungrige Giraffe!"]
                },
                "berufswitze": {
                    "patterns": ["Einen Witz ueber Programmierer.", "Witze ueber Aerzte.", "Einen Witz ueber Lehrer.", "Berufsbezogener Witz.", "Witz ueber {Beruf}.", "Noch einen {Beruf}-Witz."],
                    "responses": ["Was ist das Lieblingsessen von Programmierern? Chips mit Quellcode!", "Warum sind Aerzte so schlecht im Lotto? Weil sie nur auf 'Nieren' gehen!", "Was ist ein Lehrer mit nur einem Auge? Ein guter Schuetze!", "Warum werden Maurer nicht mu.de? Weil sie Steine fressen!"]
                },
                "flachwitze": {
                    "patterns": ["Einen Flachwitz bitte.", "Gib mir einen schlechten Witz.", "Noch einen Flachwitz.", "Einen sehr einfachen Witz.", "Kurzer Witz.", "Bitte einen Witz ohne tiefen Sinn."],
                    "responses": ["Was ist ein Keks unter einem Baum? Ein unterholzter Keks!", "Treffen sich zwei Schafe auf der Weide. Sagt das eine: 'Maeh!' Sagt das andere: 'Das wollte ich gerade sagen!'", "Warum hat der Taucher keine Freunde? Weil er auf Grund geht.", "Was ist rot und riecht nach Farbe? Rote Farbe!"]
                },
                "wortspiele": {
                    "patterns": ["Kennst du gute Wortspiele?", "Einen Kalauer bitte.", "Lustiges Wortspiel.", "Kannst du mir ein Wortspiel erzaehlen?", "Ein cleveres Wortspiel."],
                    "responses": ["Warum hat der Mathematiker einen BH an? Weil er Formeln halten muss!", "Was ist der Unterschied zwischen einem Koch und einem Politiker? Der Koch wendet sich zum Publikum und sagt: 'Guten Appetit!' Der Politiker wendet sich zum Volk und sagt: 'Guten Appetit!'", "Was ist gruen und laeuft durch den Garten? Ein Rasen-Stier!"]
                },
                "alltags_witze": {
                    "patterns": ["Einen Witz ueber das Leben.", "Lustiges aus dem Alltag.", "Witz ueber den Alltag.", "Noch ein Alltagswitz."],
                    "responses": ["Warum hat der Fahrstuhl einen Job? Weil er hoch und runter kann!", "Mein Bett und ich haben eine Hassliebe. Ich hasse es, es zu verlassen, und es hasst es, mich gehen zu lassen.", "Ich bin nicht faul, ich bin im Energiesparmodus.", "Was ist der Lieblingssport der Ameisen? Picknick!"]
                },
                "schwarzer_humor": {
                    "patterns": ["Einen Witz mit schwarzem Humor.", "Etwas makaberes.", "Darf es etwas dunkler sein?", "Witz ueber den Tod.", "Einen zynischen Witz.", "Etwas Boeses."],
                    "responses": ["Was ist der Unterschied zwischen einer Pizza und einem Taxifahrer? Eine Pizza kann eine Familie ernaehren.", "Meine Oma hat immer gesagt, 'Lebe jeden Tag, als waere es dein letzter.' Ich glaube, sie meinte das nicht woertlich, als sie die Bank ueberfallen hat.", "Warum ist der Friedhof so beliebt? Weil da alle tot sind!"]
                }
            }
        },
        "sportarten": {
            "description": "Fragen zu Sportarten und Athleten.",
            "sub_topics": {
                "fussball_allgemein": {
                    "patterns": ["Erzaehl mir etwas ueber Fussball.", "Wie viele Spieler sind in einer Fussballmannschaft?", "Fussballregeln erklaeren.", "Geschichte des Fussballs.", "Alles zum Thema Fussball.", "Grundlagen Fussball.", "Wann wurde Fussball erfunden?", "Wichtige Fussballturniere."],
                    "responses": ["Fussball ist die beliebteste Sportart der Welt.", "Eine Fussballmannschaft besteht aus 11 Spielern.", "Die Grundregeln des Fussballs sind einfach zu verstehen.", "Fussball wurde im [Jahr] in [Land] erfunden.", "Die wichtigsten Fussballturniere sind [Turnierliste]."]
                },
                "fussball_ligen": {
                    "patterns": ["Wer ist Tabellenfuehrer in der Bundesliga?", "Aktuelle Ergebnisse der Premier League.", "Wer hat die Champions League gewonnen?", "Stand in der {Liga}?", "Neueste Fussballergebnisse.", "Wer ist Meister geworden?", "Wer steigt in der {Liga} ab?", "Aktueller Stand der {Liga}."],
                    "responses": ["Der aktuelle Tabellenfuehrer in der Bundesliga ist [Team].", "Die Ergebnisse der Premier League sind [Ergebnisse].", "Die Champions League wurde zuletzt von [Team] gewonnen.", "{Team} ist Meister in {Liga} geworden.", "Aktueller Stand in der {Liga}: [Stand]."]
                },
                "basketball_allgemein": {
                    "patterns": ["Wie funktioniert Basketball?", "Regeln fuer Basketball.", "Wer ist der beste Basketballspieler?", "Geschichte des Basketballs?", "Alles ueber Basketball.", "NBA Informationen.", "Basketball Positionen."],
                    "responses": ["Basketball wird mit zwei Teams gespielt, die versuchen, Baelle in den Korb des Gegners zu werfen.", "Die Regeln sind einfach: Ziel ist es, den Ball durch den Korb zu werfen.", "Michael Jordan gilt als einer der groessten Basketballspieler aller Zeiten.", "Eine Basketballmannschaft hat [Anzahl] Spieler auf dem Feld."]
                },
                "tennis_allgemein": {
                    "patterns": ["Wer ist der beste Tennisspieler?", "Wann ist Wimbledon?", "Wie funktioniert Tennis?", "Grand Slam Turniere?", "Tennisregeln.", "Aktuelle Tennis Weltrangliste.", "Beruehmte Tennisspieler."],
                    "responses": ["Der beste Tennisspieler aktuell ist [Spielername].", "Wimbledon ist eines der vier Grand-Slam-Turniere und findet im Juli statt.", "Tennis wird mit Schlaeger und Ball gespielt.", "Die vier Grand Slams sind [Liste]."]
                },
                "formel1_allgemein": {
                    "patterns": ["Wer hat die Formel 1 Weltmeisterschaft gewonnen?", "Naechstes Formel 1 Rennen.", "Formel 1 Ergebnisse.", "Regeln der Formel 1?", "Alles zur Formel 1.", "Aktuelle Formel 1 Nachrichten.", "Formel 1 Strecken."],
                    "responses": ["Der letzte Formel 1 Weltmeister war [Fahrer].", "Das naechste Formel 1 Rennen findet am [Datum] in [Ort] statt.", "Die Formel 1 ist die Koenigsklasse des Motorsports.", "Die Regeln der Formel 1 sind komplex und betreffen [Regeln]."]
                },
                "sportler_infos": {
                    "patterns": ["Wer ist {Sportlername}?", "Biografie von {Sportlername}.", "Erfolge von {Sportlername}?", "Wie alt ist {Sportlername}?", "Lebenslauf von {Sportlername}.", "Was hat {Sportlername} erreicht?", "Ueber {Sportlername}.", "Geburtsdatum von {Sportlername}?"],
                    "responses": ["{Sportlername} ist ein bekannter [Sportart]-Spieler.", "Die Erfolge von {Sportlername} umfassen [Erfolge].", "Die Biografie von {Sportlername} ist sehr interessant.", "{Sportlername} wurde am [Datum] geboren."]
                },
                "olympische_spiele": {
                    "patterns": ["Wann sind die naechsten Olympischen Spiele?", "Wo waren die letzten Olympischen Spiele?", "Geschichte der Olympischen Spiele?", "Was ist das olympische Motto?", "Sommerspiele vs Winterspiele.", "Ueber die Olympischen Spiele.", "Welche Sportarten gibt es bei Olympia?"],
                    "responses": ["Die naechsten Olympischen Spiele sind in [Ort] im Jahr [Jahr].", "Das olympische Motto lautet 'Citius, Altius, Fortius' (Schneller, hoeher, staerker).", "Die Olympischen Spiele finden alle vier Jahre statt.", "Bei den Olympischen Spielen gibt es [Anzahl] Sportarten."]
                },
                "extremsport": {
                    "patterns": ["Was ist Base-Jumping?", "Erklaere Freeclimbing.", "Gibt es Extremsportarten in Deutschland?", "Adrenalin Sportarten.", "Risikoreiche Sportarten.", "Arten von Extremsport."],
                    "responses": ["Base-Jumping ist eine Extremsportart, bei der man von festen Objekten springt.", "Extremsportarten erfordern hohes Risiko und Koerperbeherrschung.", "Freeclimbing ist Klettern ohne Sicherung.", "Beispiele fuer Extremsport sind [Beispiele]."]
                },
                "sport_training": {
                    "patterns": ["Trainingsplan fuer {Sportart}.", "Wie baue ich Muskeln auf?", "Ausdauertraining Tipps.", "Aufwaermuebungen fuer {Sportart}.", "Dehnuebungen nach dem Training.", "Erholung nach dem Training.", "Uebungen fuer {Koerperteil}.", "Trainingsplaene fuer {Ziel}.", "Was ist Intervalltraining?", "Wie laufe ich einen Marathon?", "Fitnessroutine.", "Beste Trainingsmethoden."],
                    "responses": ["Hier ist ein Trainingsplan fuer {Sportart}: [Plan].", "Fuer {Ziel} empfehle ich folgende Uebungen: [Uebungen].", "Muskelaufbau erfordert Konsistenz und die richtige Ernaehrung.", "Ausdauertraining staerkt das Herz-Kreislauf-System."]
                },
                "sport_regeln": {
                    "patterns": ["Regeln von Fussball.", "Wie funktioniert Basketball?", "Die Regeln von {Sportart}.", "Was ist ein Offside im Eishockey?", "Grundlagen des Golfs.", "Badminton Regeln.", "Tennis Punktesystem.", "Regeln fuer {Spiel}.", "Wie viele Spieler hat ein Handballteam?", "Die Abseitsregel erklaert.", "Das Regelwerk von {Sportart}."],
                    "responses": ["Ich erklaere dir gerne die Regeln von {Sportart}.", "Die Regeln sind wie folgt: [Regelerklaerung].", "Die Abseitsregel im Fussball ist [Erklaerung].", "Ein Handballteam hat [Anzahl] Spieler auf dem Feld."]
                }
            }
        },
        "historische_ereignisse": {
            "description": "Fragen zu wichtigen historischen Ereignissen und Figuren.",
            "sub_topics": {
                "antike": {
                    "patterns": ["Erzaehl mir ueber das Roemische Reich.", "Was geschah im alten Aegypten?", "Griechenland in der Antike?", "Beruehmte Persoenlichkeiten der Antike?", "Geschichte des antiken Roms.", "Zivilisationen der Antike.", "Was ist die Akropolis?", "Wer war Kleopatra?"],
                    "responses": ["Das Roemische Reich war eine der groessten Zivilisationen der Geschichte.", "Das alte Aegypten ist bekannt fuer seine Pyramiden und Pharaonen.", "Die Antike ist eine faszinierende Epoche.", "Die Akropolis ist eine alte Festung in Athen."]
                },
                "mittelalter": {
                    "patterns": ["Die Zeit der Ritter.", "Wer war Karl der Grosse?", "Kreuzzuege erklaeren?", "Leben im Mittelalter?", "Feudalismus erklaeren.", "Burgen im Mittelalter.", "Was war die Pest?", "Das Heilige Roemische Reich."],
                    "responses": ["Das Mittelalter war eine Epoche zwischen der Antike und der Neuzeit.", "Karl der Grosse war ein bedeutender Herrscher des Mittelalters.", "Die Ritter spielten eine wichtige Rolle im Mittelalter.", "Die Pest war eine verheerende Seuche im Mittelalter."]
                },
                "neuzeit": {
                    "patterns": ["Wann war die franzoesische Revolution?", "Details zur Industriellen Revolution.", "Was war die Aufklaerung?", "Amerikanische Revolution?", "Die Renaissance.", "Entwicklung der Neuzeit.", "Die Entdeckung Amerikas.", "Der Dreissigjaehrige Krieg."],
                    "responses": ["Die franzoesische Revolution begann 1789.", "Die Industrielle Revolution fuehrte zu tiefgreifenden Veraenderungen in der Gesellschaft.", "Die Aufklaerung war eine geistige Bewegung.", "Amerika wurde 1492 entdeckt."]
                },
                "weltkriege": {
                    "patterns": ["Was war der Erste Weltkrieg?", "Ursachen des Zweiten Weltkriegs.", "Wann endete der Zweite Weltkrieg?", "Wichtige Schlachten der Weltkriege?", "Folgen der Weltkriege.", "Ueber den Ersten Weltkrieg.", "Der Holocaust.", "Pearl Harbor."],
                    "responses": ["Der Erste Weltkrieg dauerte von 1914 bis 1918.", "Der Zweite Weltkrieg endete 1945 mit der Kapitulation Deutschlands und Japans.", "Die Ursachen der Weltkriege waren komplex.", "Der Holocaust war ein Voelkermord im Zweiten Weltkrieg."]
                },
                "kalter_krieg": {
                    "patterns": ["Die Berliner Mauer.", "Was war der Kalte Krieg?", "Kubakrise erklaeren?", "Wann fiel die Berliner Mauer?", "Ueber den Kalten Krieg.", "Ereignisse im Kalten Krieg.", "NATO und Warschauer Pakt."],
                    "responses": ["Der Kalte Krieg war ein Konflikt zwischen dem Ostblock und dem Westblock.", "Die Berliner Mauer fiel am 9. November 1989.", "Die Kubakrise war eine Hoehepunkt des Kalten Krieges.", "NATO und Warschauer Pakt waren Buendnisse im Kalten Krieg."]
                },
                "entdeckungen": {
                    "patterns": ["Wer entdeckte Amerika?", "Die Seidenstrasse.", "Magellan Weltumseglung?", "Die Entdeckung der DNA?", "Grosse Entdeckungsreisen.", "Wissenschaftliche Entdeckungen.", "Wer entdeckte das Penicillin?", "Die Entdeckung des Atoms."],
                    "responses": ["Christoph Kolumbus entdeckte 1492 Amerika.", "Die Seidenstrasse war ein wichtiges Handelsnetzwerk.", "Ferdinand Magellan unternahm die erste Weltumseglung.", "Alexander Fleming entdeckte Penicillin."]
                },
                "wichtige_figuren": {
                    "patterns": ["Wer war {historische Person}?", "Biografie von {Person}.", "Die Rolle von {Person} in {Ereignis}.", "Beruehmte Koeniginnen und Koenige.", "Wissenschaftler des {Jahrhundert}.", "Kuenstler der Renaissance.", "Wer war Albert Einstein?", "Das Leben von Marie Curie.", "Beruehmte Entdecker.", "Philosophen der Antike.", "Ueber {Name}."],
                    "responses": ["{Person} war eine wichtige Figur in der Geschichte. [Biografie].", "Ueber {Person} gibt es viel zu wissen. Hier sind die Hauptfakten: [Fakten].", "Die wichtigsten Stationen im Leben von {Person} sind [Stationen].", "{Person} war bekannt fuer [Leistung]."]
                }
            }
        },
        "technologie": {
            "description": "Fragen zu verschiedenen Technologiebereichen.",
            "sub_topics": {
                "kuenstliche_intelligenz": {
                    "patterns": ["Was ist KI?", "Erklaere maschinelles Lernen.", "Anwendungen von KI.", "Was ist Deep Learning?", "Unterschied zwischen KI und Machine Learning?", "Zukunft der KI.", "KI-Modelle.", "Was ist neuronale Netze?", "Generative KI."],
                    "responses": ["KI ist ein weites Feld der Informatik.", "Maschinelles Lernen ermoeglicht Systemen, aus Daten zu lernen.", "Deep Learning ist eine Unterform des maschinellen Lernens.", "Neuronale Netze sind das Herzstueck vieler KI-Systeme."]
                },
                "quantencomputing": {
                    "patterns": ["Wie funktioniert Quantencomputing?", "Was ist ein Quantencomputer?", "Anwendungen von Quantencomputing?", "Qubits erklaeren.", "Vorteile von Quantencomputern.", "Herausforderungen im Quantencomputing."],
                    "responses": ["Quantencomputing nutzt Prinzipien der Quantenmechanik fuer Berechnungen.", "Ein Quantencomputer nutzt Qubits anstelle von Bits.", "Quantencomputing ist noch in den Anfaengen.", "Qubits sind die grundlegenden Recheneinheiten."]
                },
                "raumfahrt": {
                    "patterns": ["Aktuelle Mars-Missionen.", "Wer war der erste Mensch im Weltall?", "Internationale Raumstation (ISS)?", "Zukunft der Raumfahrt?", "SpaceX Projekte?", "Mondlandungen.", "Planetenforschung.", "Das Universum erforschen.", "Beruehmte Raumfahrer."],
                    "responses": ["Aktuell gibt es mehrere Missionen zum Mars.", "Juri Gagarin war der erste Mensch im Weltall.", "Die Raumfahrt erforscht das Universum.", "Die ISS ist ein bemanntes Raumfahrtlabor."]
                },
                "smartphones": {
                    "patterns": ["Neueste Smartphone-Modelle.", "Tipps fuer mein Handy.", "Wie finde ich ein gutes Smartphone?", "Betriebssysteme fuer Smartphones?", "Smartphone Kaufberatung.", "Handy Funktionen.", "Smartphone Trends."],
                    "responses": ["Die neuesten Smartphone-Modelle bieten [Features].", "Hier sind einige Tipps, um dein Handy zu optimieren.", "Android und iOS sind die dominanten Smartphone-Betriebssysteme.", "Ein gutes Smartphone sollte [Eigenschaften] haben."]
                },
                "internet_der_dinge": {
                    "patterns": ["Was ist IoT?", "Beispiele fuer Smart Home Geraete.", "Vorteile von IoT?", "Sicherheitsrisiken bei IoT?", "IoT Anwendungen.", "Smart Home Automation.", "Vernetzte Geraete."],
                    "responses": ["IoT verbindet physische Geraete mit dem Internet.", "Smart Home Geraete wie [Beispiel] nutzen IoT.", "IoT bietet viele Moeglichkeiten zur Automatisierung.", "Sicherheitsrisiken im IoT muessen beachtet werden."]
                },
                "erneuerbare_energien": {
                    "patterns": ["Was ist Solarenergie?", "Vorteile von Windkraft.", "Arten von erneuerbaren Energien?", "Wie funktioniert Geothermie?", "Nachhaltige Energiequellen.", "Energieerzeugung.", "Batteriespeicher.", "Energiewende."],
                    "responses": ["Solarenergie nutzt Sonnenlicht zur Stromerzeugung.", "Erneuerbare Energien sind ein Schluessel fuer eine nachhaltige Zukunft.", "Windkraft ist eine saubere Energiequelle.", "Geothermie nutzt Erdwaerme zur Energiegewinnung."]
                },
                "cyber_sicherheit": {
                    "patterns": ["Was ist Hacking?", "Wie schuetze ich meine Daten online?", "Was ist ein Virus?", "Phishing erkennen?", "Beste Antivirensoftware?", "Passwortsicherheit.", "Datenschutz im Internet.", "Cyberangriffe verhindern.", "Firewall erklaeren."],
                    "responses": ["Hacking bezeichnet das unautorisierte Eindringen in Computersysteme.", "Um deine Daten zu schuetzen, nutze starke Passwoerter und Zwei-Faktor-Authentifizierung.", "Phishing ist ein Betrugsversuch im Internet.", "Eine Firewall schuetzt Netzwerke."]
                },
                "programmierung": {
                    "patterns": ["Welche Programmiersprache soll ich lernen?", "Grundlagen der Programmierung.", "Was ist ein Algorithmus?", "Wie funktioniert Softwareentwicklung?", "Beste IDEs fuer {Sprache}?", "Webentwicklung lernen.", "Datenbanken in der Programmierung.", "DevOps erklaeren."],
                    "responses": ["Die Wahl der Programmiersprache haengt von deinem Ziel ab.", "Programmierung ist die Kunst, Computern Anweisungen zu geben.", "Ein Algorithmus ist eine Schritt-fuer-Schritt-Anleitung zur Loesung eines Problems.", "Softwareentwicklung umfasst [Phasen]."]
                }
            }
        },
        "kunst_kultur": {
            "description": "Fragen zu Kunstformen, Musik, Literatur und Film.",
            "sub_topics": {
                "malerei": {
                    "patterns": ["Wer war Vincent van Gogh?", "Stile der Malerei.", "Beruehmte Gemaelde?", "Moderne Kunst erklaeren?", "Impressionismus erklaeren.", "Renaissance Malerei.", "Kuenstler des Barocks.", "Techniken der Malerei."],
                    "responses": ["Vincent van Gogh war ein niederlaendischer Maler.", "Bekannte Malstile sind [Stile].", "Die Mona Lisa ist ein beruehmtes Gemaelde von Leonardo da Vinci.", "Impressionismus ist ein Kunststil des 19. Jahrhunderts."]
                },
                "musikgenres": {
                    "patterns": ["Was ist Jazz?", "Geschichte des Rocks.", "Merkmale von Klassik?", "Beliebte Pop-Kuenstler?", "Blues Musik.", "Elektronische Musik.", "Hip Hop Geschichte.", "Heavy Metal Merkmale."],
                    "responses": ["Jazz ist ein Musikgenre, das um 1900 in den USA entstand.", "Rockmusik entwickelte sich in den 1950er Jahren.", "Klassische Musik umfasst verschiedene Epochen.", "Elektronische Musik nutzt Synthesizer."]
                },
                "literatur": {
                    "patterns": ["Klassiker der Weltliteratur.", "Wer schrieb Hamlet?", "Was ist ein Sonett?", "Deutsche Literaten?", "Epochen der Literatur.", "Buecher empfehlungen.", "Was ist eine Novelle?", "Literarische Figuren."],
                    "responses": ["Hamlet wurde von William Shakespeare geschrieben.", "Klassiker wie [Buecher] sind zeitlos.", "Ein Sonett ist eine Gedichtform.", "Die Romantik war eine Epoche der Literatur."]
                },
                "filme": {
                    "patterns": ["Beste Filme aller Zeiten.", "Was ist ein Film-Noir?", "Regisseure von {Film}?", "Neue Kinofilme?", "Filmgenres.", "Filmproduktion.", "Oskar-Gewinner.", "Animationsfilme."],
                    "responses": ["Ein Film-Noir ist ein Filmgenre mit dunkler Atmosphaere.", "Die besten Filme sind oft Geschmackssache, aber [Film] ist hoch angesehen.", "Filmproduktion umfasst viele Schritte.", "Filme werden in verschiedene Genres eingeteilt."]
                },
                "fotografie": {
                    "patterns": ["Tipps fuer bessere Fotos.", "Was ist die Goldene Stunde in der Fotografie?", "Arten von Kameras?", "Grundlagen der Portraetfotografie?", "Landschaftsfotografie.", "Fotobearbeitungsprogramme.", "Blende, Belichtungszeit, ISO erklaeren."],
                    "responses": ["Fuer bessere Fotos achte auf Licht und Komposition.", "Die Goldene Stunde ist die Zeit kurz nach Sonnenaufgang oder vor Sonnenuntergang.", "Es gibt digitale und analoge Kameras.", "Blende, Belichtungszeit und ISO sind die Belichtungsparameter."]
                },
                "theater": {
                    "patterns": ["Was ist Theater?", "Beruehmte Theaterstuecke.", "Geschichte des Theaters.", "Musical Empfehlungen.", "Dramaturgie erklaeren.", "Opern erklaeren."],
                    "responses": ["Theater ist eine darstellende Kunst.", "Beruehmte Theaterstuecke sind zum Beispiel [Stuecke].", "Musicals kombinieren Gesang, Tanz und Schauspiel.", "Dramaturgie befasst sich mit der Struktur von Theaterstuecken."]
                },
                "architektur": {
                    "patterns": ["Was ist der Baustil {Stil}?", "Beruehmte Gebaeude.", "Geschichte der Architektur.", "Moderne Architektur.", "Antike Bauwerke.", "Gotische Architektur."],
                    "responses": ["Der Baustil {Stil} zeichnet sich durch [Merkmale] aus.", "Der Eiffelturm ist ein bekanntes Architekturensemble.", "Architektur hat sich ueber Jahrtausende entwickelt.", "Gotische Architektur ist bekannt fuer ihre Spitzboegen."]
                }
            }
        },
        "gesundheit_medizin": {
            "description": "Informationen zu Gesundheit, Krankheiten und medizinischen Behandlungen.",
            "sub_topics": {
                "allgemeine_gesundheit": {
                    "patterns": ["Tipps fuer ein gesundes Leben.", "Wie wichtig ist Schlaf?", "Gesunde Ernaehrung?", "Stress reduzieren?", "Bewegung im Alltag.", "Wohlbefinden steigern.", "Mentale Gesundheit.", "Immunstaerkung."],
                    "responses": ["Ein gesunder Lebensstil umfasst ausgewogene Ernaehrung, Bewegung und ausreichend Schlaf.", "Schlaf ist entscheidend fuer die koerperliche und geistige Erholung.", "Regelmaessige Bewegung staerkt den Koerper.", "Mentale Gesundheit ist ebenso wichtig wie koerperliche Gesundheit."]
                },
                "erkrankungen": {
                    "patterns": ["Symptome von Diabetes.", "Was ist eine Grippe?", "Ursachen von Kopfschmerzen?", "Wie behandelt man eine Erkaeltung?", "What ist Bluthochdruck?", "Allergien erklaeren.", "Herzinfarkt Symptome.", "Krebsarten."],
                    "responses": ["Die Symptome von Diabetes koennen [Symptome] umfassen.", "Eine Grippe ist eine virale Infektion der Atemwege.", "Kopfschmerzen koennen viele Ursachen haben.", "Allergien sind Ueberreaktionen des Immunsystems."]
                },
                "behandlungen": {
                    "patterns": ["Therapiemoeglichkeiten bei Krebs.", "Wie wirken Antibiotika?", "Was ist eine Operation?", "Moderne medizinische Behandlungen?", "Impfungen erklaeren.", "Alternativmedizin.", "Physiotherapie.", "Rehabilitation."],
                    "responses": ["Die Behandlung von Krebs haengt vom Typ und Stadium ab.", "Antibiotika bekaempfen bakterielle Infektionen.", "Operationen sind chirurgische Eingriffe.", "Impfungen schuetzen vor Krankheiten."]
                },
                "ernaerung": {
                    "patterns": ["Was ist gesunde Ernaehrung?", "Vitamine und ihre Bedeutung.", "Wichtige Mineralstoffe?", "Vegetarische Ernaehrung Vorteile?", "Vegane Ernaehrung.", "Naehrwerte von {Lebensmittel}.", "Superfoods.", "Darmgesundheit."],
                    "responses": ["Gesunde Ernaehrung bedeutet, alle notwendigen Naehrstoffe zu sich zu nehmen.", "Vitamine sind essentiell fuer viele Koerperfunktionen.", "Vegetarische Ernaehrung kann viele Vorteile haben.", "Mineralstoffe sind wichtig fuer den Koerper."]
                },
                "fitness_sport": {
                    "patterns": ["Effektive Sportuebungen.", "Trainingsplan fuer Anfaenger.", "Was ist Ausdauertraining?", "Krafttraining Tipps?", "Yoga fuer Ruecken.", "Fitness im Alter.", "Muskelaufbau.", "Abnehmen durch Sport."],
                    "responses": ["Effektive Sportuebungen sind [Beispiele].", "Ein Trainingsplan fuer Anfaenger sollte [Inhalt] beinhalten.", "Ausdauertraining verbessert die Herz-Kreislauf-Funktion.", "Yoga staerkt Koerper und Geist."]
                },
                "psychische_gesundheit": {
                    "patterns": ["Was ist Depression?", "Tipps gegen Angstzustaende.", "Burnout erkennen?", "Wie finde ich einen Therapeuten?", "Mentale Staerke aufbauen.", "Stressbewaeltigung.", "Psychische Stoerungen.", "Therapieformen."],
                    "responses": ["Depression ist eine ernsthafte psychische Erkrankung.", "Bei Angstzustaenden koennen Entspannungstechniken helfen.", "Einen Therapeuten findest du ueber [Wege].", "Stressbewaeltigung hilft, das Wohlbefinden zu erhalten."]
                }
            }
        },
        "wissenschaft": {
            "description": "Erklaerungen zu naturwissenschaftlichen Phaenomenen und Theorien.",
            "sub_topics": {
                "physik": {
                    "patterns": ["Was ist die Relativitaetstheorie?", "Erklaere die Schwerkraft.", "Quantenphysik einfach erklaert.", "Die Gesetze der Thermodynamik?", "Was ist dunkle Materie?", "Physikalische Grundgesetze.", "Schall und Licht.", "Elektrizitaet."],
                    "responses": ["Die Relativitaetstheorie wurde von Albert Einstein entwickelt.", "Schwerkraft ist die Kraft, die Massen anzieht.", "Die Thermodynamik beschaeftigt sich mit Waerme und Energie.", "Quantenphysik erklaert die Welt der Atome."]
                },
                "chemie": {
                    "patterns": ["Was ist ein Element?", "Wie funktioniert Photosynthese?", "Arten von chemischen Bindungen?", "Das Periodensystem erklaeren?", "Sauren und Basen.", "Chemische Reaktionen.", "Organische Chemie.", "Alchemie Geschichte."],
                    "responses": ["Ein Element ist ein Stoff, der nicht in einfachere Stoffe zerlegt werden kann.", "Photosynthese ist der Prozess, bei dem Pflanzen Energie aus Licht gewinnen.", "Chemische Bindungen halten Atome zusammen.", "Das Periodensystem ordnet die Elemente."]
                },
                "biologie": {
                    "patterns": ["Was ist DNA?", "Wie funktioniert die Zellteilung?", "Evolutionstheorie erklaeren?", "Die menschliche Anatomie?", "Genetik Grundlagen.", "Oekologie erklaeren.", "Viren und Bakterien.", "Pflanzenphysiologie."],
                    "responses": ["DNA enthaelt die genetischen Informationen eines Organismus.", "Die Zellteilung ist der Prozess, bei dem sich Zellen vermehren.", "Die Evolutionstheorie erklaert die Entwicklung des Lebens.", "Oekologie ist die Lehre von den Beziehungen der Lebewesen zur Umwelt."]
                },
                "astronomie": {
                    "patterns": ["Was ist ein schwarzes Loch?", "Planeten unseres Sonnensystems.", "Galaxien und Sterne?", "Die Entstehung des Universums?", "Supernova erklaeren.", "Kometen und Asteroiden.", "Exoplaneten.", "Teleskope."],
                    "responses": ["Ein schwarzes Loch ist ein Bereich im Raum, aus dem nichts entkommen kann.", "Unser Sonnensystem besteht aus [Anzahl] Planeten.", "Galaxien sind Ansammlungen von Sternen.", "Exoplaneten sind Planeten ausserhalb unseres Sonnensystems."]
                },
                "geologie": {
                    "patterns": ["Wie entstehen Erdbeben?", "Was sind Vulkane?", "Arten von Gesteinen?", "Kontinentalverschiebung erklaeren?", "Erdgeschichte.", "Mineralien.", "Gebirgsbildung.", "Wuestenbildung."],
                    "responses": ["Erdbeben entstehen durch die Bewegung tektonischer Platten.", "Vulkane sind Oeffnungen in der Erdkruste, durch die Magma austritt.", "Gesteine werden in verschiedene Typen unterteilt.", "Die Erdgeschichte ist in Aeonen unterteilt."]
                },
                "mathematik": {
                    "patterns": ["Was ist Pi?", "Erklaere den Satz des Pythagoras.", "Was ist Algebra?", "Grundlagen der Geometrie?", "Differentialrechnung erklaeren.", "Statistik Grundlagen.", "Wahrscheinlichkeitsrechnung.", "Logik in der Mathematik."],
                    "responses": ["Pi ist eine mathematische Konstante.", "Der Satz des Pythagoras beschreibt die Beziehung zwischen den Seiten eines rechtwinkligen Dreiecks.", "Algebra befasst sich mit Symbolen und den Regeln, sie zu manipulieren.", "Geometrie ist die Lehre von Formen und Raeumen."]
                }
            }
        },
        "umwelt_natur": {
            "description": "Fragen zum Umweltschutz, Klimawandel und Naturphaenomenen.",
            "sub_topics": {
                "klimawandel": {
                    "patterns": ["Ursachen des Klimawandels.", "Folgen des Klimawandels.", "Wie kann man den Klimawandel bekaempfen?", "Was ist der Treibhauseffekt?", "Globale Erwaermung.", "Klima-Loesungen.", "CO2 Ausstoss reduzieren.", "Klimaziele."],
                    "responses": ["Die Hauptursachen des Klimawandels sind [Ursachen].", "Die Folgen des Klimawandels umfassen [Folgen].", "Der Treibhauseffekt ist ein natuerliches Phaenomen.", "Wir koennen den Klimawandel durch [Massnahmen] bekaempfen."]
                },
                "umweltschutz": {
                    "patterns": ["Wie kann ich die Umwelt schuetzen?", "Recycling-Tipps.", "Was ist nachhaltige Entwicklung?", "Beste Umweltschutzorganisationen?", "Plastikmuell reduzieren.", "Ressourcenschonung.", "Wasser sparen.", "Luftverschmutzung."],
                    "responses": ["Du kannst die Umwelt schuetzen, indem du [Tipps].", "Recycling ist wichtig, um Ressourcen zu schonen.", "Nachhaltige Entwicklung bedeutet, die Beduerfnisse der Gegenwart zu befriedigen, ohne zukuenftige Generationen zu gefaehrden.", "Umweltschutz ist eine globale Aufgabe."]
                },
                "oekosysteme": {
                    "patterns": ["Was ist ein Oekosystem?", "Arten von Oekosystemen.", "Wie funktionieren Nahrungsketten?", "Die Bedeutung von Biodiversitaet?", "Wald Oekosystem.", "Meer Oekosystem.", "Riff Oekosystem.", "Stadtoekosystem."],
                    "responses": ["Ein Oekosystem ist ein System aus Lebewesen und ihrer Umwelt.", "Es gibt verschiedene Arten von Oekosystemen, wie [Beispiele].", "Nahrungsketten beschreiben die Energieuebertragung.", "Biodiversitaet ist die Vielfalt des Lebens auf der Erde."]
                },
                "tierarten": {
                    "patterns": ["Informationen ueber Loewe.", "Bedrohte Tierarten.", "Wo leben Pinguine?", "Verhalten von {Tierart}?", "Wandernde Tierarten.", "Tiere im Regenwald.", "Meerestiere.", "Voegelarten."],
                    "responses": ["Loewen sind grosse Raubkatzen, die in Afrika leben.", "Es gibt viele bedrohte Tierarten, zum Beispiel [Arten].", "Pinguine leben in der Antarktis.", "Das Verhalten von [Tierart] ist [Beschreibung]."]
                },
                "pflanzen": {
                    "patterns": ["Wie pflege ich eine Orchidee?", "Pflanzen fuer den Garten.", "Was ist Photosynthese bei Pflanzen?", "Heilpflanzen?", "Pflanzen bestimmen.", "Baumarten.", "Blumenarten.", "Krauter."],
                    "responses": ["Orchideen benoetigen [Pflegehinweise].", "Pflanzen wie [Pflanzenart] eignen sich gut fuer den Garten.", "Heilpflanzen werden in der Medizin verwendet.", "Photosynthese ist der Prozess, bei dem Pflanzen Energie produzieren."]
                },
                "naturkatastrophen": {
                    "patterns": ["Was sind Tsunamis?", "Wie entstehen Erdbeben?", "Was ist ein Vulkan?", "Hurrikan-Warnungen?", "Ueberschwemmungen.", "Tornados.", "Lawinen.", "Duerren."],
                    "responses": ["Tsunamis sind grosse Wellen, die durch Unterwasser-Erdbeben ausgeloest werden.", "Erdbeben entstehen durch die Bewegung tektonischer Platten.", "Vulkane sind Oeffnungen in der Erdkruste.", "Hurrikane sind tropische Wirbelstuerme."]
                }
            }
        },
        "wirtschaft_finanzen": {
            "description": "Fragen zur Wirtschaft, Geldanlage und Finanzthemen.",
            "sub_topics": {
                "aktienmarkt": {
                    "patterns": ["Wie kaufe ich Aktien?", "Was ist der DAX?", "Investieren in den Aktienmarkt?", "Risiken von Aktien?", "Boerse erklaeren.", "Aktienkurse heute.", "Was ist eine Anleihe?", "Derivate erklaeren."],
                    "responses": ["Aktien sind Anteile an einem Unternehmen.", "Der DAX ist der wichtigste deutsche Aktienindex.", "Investieren am Aktienmarkt birgt Risiken.", "Eine Anleihe ist ein Schuldtitel."]
                },
                "geldanlage": {
                    "patterns": ["Geldanlage fuer Anfaenger.", "Was ist ein ETF?", "Immobilien als Geldanlage?", "Sparmoeglichkeiten?", "Anleihen erklaeren.", "Fonds vs. Aktien.", "Bausparvertrag.", "Riester-Rente."],
                    "responses": ["Fuer Anfaenger eignen sich [Anlagemoeglichkeiten].", "Ein ETF ist ein boersengehandelter Fonds.", "Immobilien koennen eine gute Geldanlage sein.", "Sparmoeglichkeiten sind vielfaeltig."]
                },
                "bankwesen": {
                    "patterns": ["Wie eroeffne ich ein Konto?", "Was ist ein Kredit?", "Online-Banking Erklaerung?", "Sicherheit im Bankwesen?", "Bankdienstleistungen.", "Girokonto erklaeren.", "Hypothek erklaeren.", "Bankleitzahl."],
                    "responses": ["Um ein Konto zu eroeffnen, benoetigst du [Dokumente].", "Ein Kredit ist eine Leihgabe von Geld.", "Online-Banking ermoeglicht dir, Bankgeschaefte online zu erledigen.", "Ein Girokonto ist fuer den taeglichen Zahlungsverkehr."]
                },
                "inflation": {
                    "patterns": ["Was ist Inflation?", "Auswirkungen von Inflation?", "Wie schuetze ich mein Geld vor Inflation?", "Inflationsrate aktuell.", "Ursachen von Inflation.", "Deflation erklaeren."],
                    "responses": ["Inflation ist der Anstieg des allgemeinen Preisniveaus fuer Gueter und Dienstleistungen.", "Inflation kann die Kaufkraft deines Geldes verringern.", "Man kann sich gegen Inflation absichern.", "Deflation ist das Gegenteil von Inflation."]
                },
                "kryptowaehrungen": {
                    "patterns": ["Was ist Bitcoin?", "Wie kaufe ich Kryptowaehrungen?", "Risiken von Krypto?", "Blockchain Erklaerung?", "Ethereum erklaeren.", "NFTs erklaeren.", "Dezentrale Finanzen (DeFi).", "Mining erklaeren."],
                    "responses": ["Bitcoin ist die bekannteste Kryptowaehrung.", "Der Kauf von Kryptowaehrungen erfolgt ueber [Plattformen].", "Blockchain ist die zugrunde liegende Technologie von Kryptowaehrungen.", "NFTs sind einzigartige digitale Vermoegenswerte."]
                }
            }
        },
        "reise_tourismus": {
            "description": "Informationen zu Reisezielen, Reiseplanung und Reisetipps.",
            "sub_topics": {
                "reiseziele": {
                    "patterns": ["Schoene Staedte in Europa.", "Beste Reiseziele im Sommer.", "Urlaubsideen fuer Familien?", "Exotische Reiseziele?", "Strandurlaub empfehlen.", "Staedtereisen.", "Skiurlaub.", "Abenteuerurlaub."],
                    "responses": ["Einige schoene Staedte in Europa sind [Staedte].", "Im Sommer sind [Ziele] besonders beliebt.", "Familienurlaub in [Ort] ist eine gute Idee.", "Exotische Reiseziele bieten einzigartige Erlebnisse."]
                },
                "sehenswuerdigkeiten": {
                    "patterns": ["Was ist der Eiffelturm?", "Interessante Fakten zur Chinesischen Mauer.", "Die Pyramiden von Gizeh?", "Beruehmte Museen in {Stadt}?", "Wahrzeichen von {Stadt}.", "Weltwunder.", "Historische Gebaeude.", "Naturwunder."],
                    "responses": ["Der Eiffelturm ist ein Wahrzeichen von Paris.", "Die Chinesische Mauer ist eines der groessten Bauwerke der Welt.", "Die Pyramiden von Gizeh sind beeindruckende Bauwerke.", "Museen in {Stadt} bieten [Ausstellungen]."]
                },
                "reisetipps": {
                    "patterns": ["Tipps fuer Fernreisen.", "Wie packe ich richtig?", "Sicherheitstipps im Ausland?", "Was tun bei Jetlag?", "Reisen mit Kindern Tipps.", "Guenstig reisen.", "Reiseversicherung.", "Visabestimmungen."],
                    "responses": ["Fuer Fernreisen solltest du [Tipps].", "Packe leicht und organisiere deine Dokumente.", "Sicherheit auf Reisen ist wichtig.", "Jetlag kann durch [Massnahmen] gemildert werden."]
                },
                "transportmittel": {
                    "patterns": ["Beste Fluggesellschaften.", "Wie reise ich guenstig mit dem Zug?", "Mietwagen im Ausland?", "Oeffentliche Verkehrsmittel in {Stadt}?", "Reisen mit Bus.", "Kreuzfahrten.", "Fahrradreisen.", "Trampen."],
                    "responses": ["Einige der besten Fluggesellschaften sind [Airlines].", "Guenstig Zug fahren kannst du mit [Tipps].", "Mietwagen bieten Flexibilitaet auf Reisen.", "Oeffentliche Verkehrsmittel sind umweltfreundlich."]
                },
                "kulinarische_reisen": {
                    "patterns": ["Beste Kuechen der Welt.", "Wo gibt es gutes Street Food?", "Kulinarische Spezialitaeten von {Land}?", "Essen in {Land}.", "Regionale Kueche.", "Food Touren.", "Michelin Sterne Restaurants."],
                    "responses": ["Die besten Kuechen der Welt sind [Kuechen].", "Street Food findest du oft in [Regionen].", "Die Spezialitaeten von {Land} sind [Spezialitaeten].", "Kulinarische Reisen bieten einzigartige Geschmackserlebnisse."]
                }
            }
        },
        "bildung_lernen": {
            "description": "Fragen zu Bildungssystemen, Lernmethoden und Studiengaengen.",
            "sub_topics": {
                "lernmethoden": {
                    "patterns": ["Wie lerne ich am effektivsten?", "Gedaechnistechniken.", "Lernstrategien fuer Pruefungen?", "Was ist aktives Lernen?", "Mind Mapping erklaeren.", "Lern-Apps.", "Effektive Lernplaene.", "Vorbereitung auf Examen."],
                    "responses": ["Effektive Lernmethoden sind [Methoden].", "Gedaechnistechniken koennen dir helfen, dich besser zu erinnern.", "Aktives Lernen verbessert das Verstaendnis.", "Ein Lernplan strukturiert das Lernen."]
                },
                "universitaeten": {
                    "patterns": ["Die besten Universitaeten in Deutschland.", "Wie bewerbe ich mich an einer Uni?", "Studiengaenge in {Fachgebiet}?", "Studieren im Ausland?", "Master Studium.", "Promotion Moeglichkeiten.", "FH vs Uni.", "Studienfinanzierung."],
                    "responses": ["Einige der besten Universitaeten in Deutschland sind [Unis].", "Fuer eine Bewerbung an einer Uni benoetigst du [Dokumente].", "Ein Studium im Ausland bietet viele Vorteile.", "Ein Masterstudium vertieft das Wissen."]
                },
                "sprachen_lernen": {
                    "patterns": ["Wie lerne ich Spanisch?", "Effektive Sprachlern-Apps.", "Tipps zum Vokabellernen?", "Wie verbessere ich meine Aussprache?", "Sprachkurse {Sprache}.", "Lernstrategien fuer Sprachen.", "Immersionsmethode.", "Sprachaustausch."],
                    "responses": ["Um Spanisch zu lernen, kannst du [Methoden] nutzen.", "Sprachlern-Apps wie [Apps] sind sehr hilfreich.", "Regelmaessiges Sprechen verbessert die Aussprache.", "Immersionsmethode ist sehr effektiv fuer Sprachen."]
                },
                "schulsysteme": {
                    "patterns": ["Wie funktioniert das Schulsystem in Deutschland?", "Unterschiede zwischen Schulformen?", "Das Bildungssystem in {Land}?", "Gymnasium vs. Realschule.", "Berufsschule erklaeren.", "Integrationsschulen.", "Schulabschluesse."],
                    "responses": ["Das deutsche Schulsystem ist in [Struktur] unterteilt.", "Die Unterschiede zwischen Schulformen liegen in [Unterschiede].", "Jedes Schulsystem hat seine Besonderheiten.", "Schulabschluesse eroeffnen verschiedene Wege."]
                },
                "forschung": {
                    "patterns": ["Was ist Forschung?", "Arten von Forschung.", "Wichtige Forschungsinstitute?", "Wie funktioniert wissenschaftliche Forschung?", "Forschungsmethoden.", "Aktuelle Forschungsergebnisse.", "Grundlagenforschung.", "Angewandte Forschung."],
                    "responses": ["Forschung ist die systematische Untersuchung von Themen.", "Es gibt grundlegende und angewandte Forschung.", "Wissenschaftliche Forschung folgt bestimmten Methoden.", "Aktuelle Forschungsergebnisse sind [Ergebnisse]."]
                }
            }
        },
        "alltag": {
            "description": "Tipps und Informationen fuer den taeglichen Gebrauch.",
            "sub_topics": {
                "kochen_backen": {
                    "patterns": ["Rezept fuer Lasagne.", "Wie backe ich Brot?", "Schnelle Rezepte fuer den Abend?", "Kuchen backen ohne Ei?", "Vegetarisches Gericht.", "Dessert Ideen.", "Suppenrezepte.", "Vegan kochen."],
                    "responses": ["Hier ist ein Rezept fuer Lasagne: [Rezept].", "Brot backen kann einfach sein, wenn du [Tipps] befolgst.", "Ein schnelles Rezept ist [Rezeptvorschlag].", "Vegetarische Gerichte sind vielseitig."]
                },
                "haushaltstipps": {
                    "patterns": ["Wie reinige ich Fenster streifenfrei?", "Putztipps fuer die Kueche.", "Waesche richtig waschen?", "Wie entferne ich Flecken aus Kleidung?", "Organisationstipps fuer den Haushalt.", "Gartenarbeit fuer Anfaenger.", "Badezimmer reinigen.", "Entkalken von Geraeten."],
                    "responses": ["Fuer streifenfreie Fenster nutze [Tipps].", "Zum Reinigen der Kueche empfehle ich [Produkte].", "Waesche nach Farben und Temperaturen sortieren.", "Flecken lassen sich mit [Mittel] entfernen."]
                },
                "freizeit_hobbys": {
                    "patterns": ["Ideen fuer neue Hobbys.", "Was kann ich am Wochenende tun?", "Sportliche Aktivitaeten in meiner Naehe?", "Kreative Hobbys?", "Entspannung nach der Arbeit.", "Outdoor-Aktivitaeten.", "Brettspiele.", "Buecher lesen."],
                    "responses": ["Einige Ideen fuer neue Hobbys sind [Hobbys].", "Am Wochenende koenntest du [Aktivitaet] unternehmen.", "Sportliche Aktivitaeten halten fit.", "Kreative Hobbys foerdern die Fantasie."]
                },
                "persoenliche_entwicklung": {
                    "patterns": ["Wie werde ich produktiver?", "Tipps zur Selbstverbesserung.", "Zeitmanagement lernen?", "Wie setze ich mir Ziele richtig?", "Selbstbewusstsein staerken.", "Positive Denkweise.", "Gewohnheiten aendern.", "Mindset verbessern."],
                    "responses": ["Um produktiver zu werden, versuche [Tipps].", "Selbstverbesserung beginnt mit [Schritt].", "Zeitmanagement hilft, den Tag zu strukturieren.", "Setze dir SMART-Ziele."]
                },
                "einkaufen": {
                    "patterns": ["Wo kaufe ich guenstig Lebensmittel?", "Tipps fuer den Online-Einkauf.", "Beste Angebote fuer Elektronik?", "Wie vergleiche ich Preise?", "Nachhaltig einkaufen.", "Mode Trends.", "Online-Shopping Sicherheit.", "Geld sparen beim Einkaufen."],
                    "responses": ["Guenstige Lebensmittel findest du bei [Geschaefte].", "Beim Online-Einkauf achte auf [Tipps].", "Preisvergleiche sparen Geld.", "Nachhaltiges Einkaufen ist gut fuer die Umwelt."]
                }
            }
        },
        "notfall_hilfe": {
            "description": "Informationen und Anleitungen fuer Notfaelle.",
            "sub_topics": {
                "erste_hilfe": {
                    "patterns": ["Was tun bei Verbrennungen?", "Wie leiste ich Erste Hilfe?", "Reanimation Anleitung?", "Was tun bei einem Schlaganfall?", "Verband anlegen.", "Hilfe bei Kreislaufproblemen.", "Erste Hilfe bei Schnittwunden.", "Notfallset Inhalt."],
                    "responses": ["Bei Verbrennungen solltest du [Massnahmen] ergreifen.", "Erste Hilfe ist entscheidend, um Leben zu retten.", "Reanimation ist bei Herz-Kreislauf-Stillstand notwendig.", "Einen Verband legst du so an: [Anleitung]."]
                },
                "notfallnummern": {
                    "patterns": ["Wie ist die Notrufnummer in Deutschland?", "Wichtige Telefonnummern im Ausland.", "Feuerwehr Notruf?", "Polizei Notruf?", "Rettungsdienst Nummer.", "Giftnotruf.", "Aerztlicher Notdienst."],
                    "responses": ["Die Notrufnummer in Deutschland ist 112.", "Wichtige Telefonnummern fuer [Land] sind [Nummern].", "Die Feuerwehr ist unter [Nummer] erreichbar.", "Der Giftnotruf ist fuer Vergiftungsfaelle."]
                },
                "katastrophenhilfe": {
                    "patterns": ["Was tun bei Hochwasser?", "Sicherheitsmassnahmen bei Erdbeben?", "Vorbereitung auf Naturkatastrophen?", "Evakuierungsplan.", "Schutz vor Sturm.", "Blackout Vorbereitung.", "Pandemie Vorsorge."],
                    "responses": ["Bei Hochwasser solltest du [Massnahmen].", "Vorbereitung ist der Schluessel im Katastrophenfall.", "Ein Evakuierungsplan ist im Katastrophenfall wichtig.", "Schutz vor Sturm beinhaltet [Massnahmen]."]
                }
            }
        },
        "lokalinformationen": {
            "description": "Fragen zu lokalen Gegebenheiten, Veranstaltungen und Dienstleistungen.",
            "sub_topics": {
                "veranstaltungen": {
                    "patterns": ["Welche Veranstaltungen gibt es in {Stadt}?", "Konzerte in Berlin.", "Festivals in {Region}?", "Ausstellungen in meiner Naehe?", "Events am Wochenende.", "Kulturelle Veranstaltungen.", "Sportevents in {Stadt}.", "Messen in {Stadt}."],
                    "responses": ["In {Stadt} gibt es folgende Veranstaltungen: [Veranstaltungen].", "Konzerte in Berlin sind [Liste].", "Festivals bieten viel Unterhaltung.", "Ausstellungen in deiner Naehe sind [Ausstellungen]."]
                },
                "restaurants": {
                    "patterns": ["Gute italienische Restaurants in meiner Naehe.", "Vegetarische Restaurants in {Stadt}.", "Beste Burger in {Stadt}?", "Restaurants mit Lieferservice?", "Cafe Empfehlungen.", "Sushi Restaurants.", "Griechische Restaurants.", "Indische Restaurants."],
                    "responses": ["Ein gutes italienisches Restaurant in deiner Naehe ist [Restaurant].", "Vegetarische Optionen findest du bei [Restaurants].", "Burger sind eine beliebte Wahl.", "Sushi Restaurants in {Stadt} sind [Liste]."]
                },
                "oeffentliche_verkehrsmittel": {
                    "patterns": ["Wie komme ich zum Hauptbahnhof?", "Fahrplan fuer {Linie}?", "Oeffentliche Verkehrsmittel in {Stadt}?", "Ticketpreise oeffentliche Verkehrsmittel?", "Busverbindungen.", "U-Bahn Netz.", "Strassenbahn Fahrplan.", "S-Bahn Verbindungen."],
                    "responses": ["Du kommst zum Hauptbahnhof mit [Verbindung].", "Der Fahrplan fuer {Linie} ist [Fahrplan].", "Oeffentliche Verkehrsmittel sind umweltfreundlich.", "Ticketpreise sind [Preise]."]
                },
                "sehenswuerdigkeiten_lokal": {
                    "patterns": ["Was sind die besten Sehenswuerdigkeiten in {Stadt}?", "Museen in {Stadt}?", "Parks in {Stadt}?", "Historische Orte in {Stadt}.", "Touristenattraktionen.", "Interessante Plaetze in {Stadt}."],
                    "responses": ["In {Stadt} gibt es viele Sehenswuerdigkeiten, zum Beispiel [Sehenswuerdigkeiten].", "Die Museen in {Stadt} sind [Liste].", "Parks bieten Erholung in der Stadt.", "Historische Orte sind [Liste]."]
                }
            }
        },
        "gaming": {
            "description": "Fragen zu Videospielen und Gaming-Hardware.",
            "sub_topics": {
                "videospiele_empfehlung": {
                    "patterns": ["Empfiehl mir ein Videospiel.", "Was soll ich spielen?", "Gute Spiele fuer {Plattform}.", "Spiele des Genres {Genre}.", "Neue Spiele Releases.", "Multiplayer-Spiele.", "Einzelspieler Spiele.", "Rollenspiele."],
                    "responses": ["Ich habe einige Videospiel-Empfehlungen fuer dich.", "Wie waere es mit [Spiel]? Es ist ein [Genre] Spiel.", "Fuer {Plattform} empfehle ich [Spiel].", "Neue Spiele wie [Spiel] sind gerade erschienen."]
                },
                "gaming_hardware": {
                    "patterns": ["Beste Gaming-PCs.", "Konsolenvergleich.", "Welche Grafikkarte ist gut?", "Gaming-Maus empfehlen.", "Gaming-Setup.", "Gaming-Monitor.", "Headset fuer Gaming."],
                    "responses": ["Die besten Gaming-PCs haben [Spezifikationen].", "Konsolen wie PlayStation und Xbox bieten unterschiedliche Vorteile.", "Eine gute Grafikkarte ist wichtig fuer Gaming.", "Ein Gaming-Setup umfasst [Komponenten]."]
                },
                "e_sport": {
                    "patterns": ["Was ist E-Sport?", "Bekannte E-Sport Teams.", "Grosse E-Sport Turniere.", "Wie werde ich E-Sportler?", "E-Sport Ligen.", "E-Sport Spiele."],
                    "responses": ["E-Sport ist kompetitives Videospielen.", "Bekannte E-Sport Teams sind [Teams].", "E-Sport Turniere haben grosse Preisgelder.", "Um E-Sportler zu werden, benoetigst du [Eigenschaften]."]
                },
                "spiel_tipps": {
                    "patterns": ["Tipps und Tricks fuer {Spiel}.", "Wie besiege ich den Boss in {Spiel}?", "Loesung fuer {Spiel} Level.", "Cheats fuer {Spiel}.", "Strategien fuer {Spiel}.", "Guides fuer {Spiel}."],
                    "responses": ["Fuer {Spiel} empfehle ich dir folgende Tricks: [Tipps].", "Um den Boss zu besiegen, versuche [Strategie].", "Es gibt viele Loesungen fuer {Spiel} Level."]
                }
            }
        },
        "filmproduktion": {
            "description": "Fragen zur Herstellung und Branche von Filmen.",
            "sub_topics": {
                "filmgenres_erklaerung": {
                    "patterns": ["Was ist ein Thriller?", "Merkmale eines Dramas.", "Erklaere Science-Fiction-Filme.", "Was macht einen guten Horrorfilm aus?", "Komoedie erklaeren.", "Dokumentarfilm."],
                    "responses": ["Ein Thriller ist ein Genre, das Spannung erzeugt.", "Ein Drama konzentriert sich auf emotionale Konflikte.", "Science-Fiction-Filme spielen oft in der Zukunft.", "Horrorfilme sollen das Publikum erschrecken."]
                },
                "regisseure_produzenten": {
                    "patterns": ["Wer ist {Regisseurname}?", "Beruehmte Filmproduzenten.", "Filme von {Regisseurname}?", "Wie wird man Regisseur?", "Rolle des Produzenten.", "Film-Awards fuer Regisseure."],
                    "responses": ["{Regisseurname} ist ein bekannter Filmregisseur.", "Ein Filmproduzent ist fuer die Finanzierung und Organisation eines Films verantwortlich.", "Filme von {Regisseurname} sind [Filme].", "Regisseure leiten die Filmproduktion."]
                },
                "schauspieler_rollen": {
                    "patterns": ["Wer ist der Hauptdarsteller in {Film}?", "In welchen Filmen hat {Schauspieler} mitgespielt?", "Biografie von {Schauspieler}?", "Wie wird man Schauspieler?", "Beruehmte Schauspieler.", "Schauspieltechniken."],
                    "responses": ["Der Hauptdarsteller in {Film} ist [Schauspielername].", "{Schauspieler} hat in vielen Filmen mitgespielt, darunter [Filme].", "Die Biografie von {Schauspieler} ist [Details].", "Schauspieler spielen Rollen in Filmen und Theaterstuecken."]
                },
                "filmtechnik": {
                    "patterns": ["Was ist ein Greenscreen?", "Wie funktionieren Spezialeffekte?", "Kameraeinstellungen beim Film.", "Was ist Postproduktion?", "Filmbeleuchtung.", "Sounddesign im Film."],
                    "responses": ["Ein Greenscreen wird fuer visuelle Effekte verwendet.", "Spezialeffekte erzeugen Illusionen im Film.", "Die Postproduktion umfasst Bearbeitung nach dem Dreh.", "Kameraeinstellungen beeinflussen die Bildsprache."]
                }
            }
        },
        "musikproduktion": {
            "description": "Fragen zur Herstellung und Branche von Musik.",
            "sub_topics": {
                "musikinstrumente": {
                    "patterns": ["Welches Musikinstrument soll ich lernen?", "Grundlagen des Gitarrenspiels.", "Wie funktioniert ein Klavier?", "Arten von Schlagzeugen.", "Geige lernen.", "Saxophon spielen."],
                    "responses": ["Die Wahl des Musikinstruments haengt von deinen Vorlieben ab.", "Gitarre spielen erfordert Uebung und Geduld.", "Ein Klavier erzeugt Toene durch Haemmer.", "Schlagzeuge sind Rhythmusinstrumente."]
                },
                "musikgenres_produktion": {
                    "patterns": ["Wie produziert man Hip-Hop?", "Merkmale von elektronischer Musikproduktion.", "Was ist Mastering in der Musik?", "Mixing erklaeren.", "Popmusik Produktion.", "Rockmusik Produktion."],
                    "responses": ["Hip-Hop-Produktion umfasst das Sampling und Beatmaking.", "Mastering ist der letzte Schritt in der Musikproduktion.", "Mixing ist das Mischen von Tonspuren.", "Elektronische Musik wird oft mit Synthesizern produziert."]
                },
                "songwriting": {
                    "patterns": ["Wie schreibe ich einen Song?", "Tipps zum Texten.", "Melodien entwickeln.", "Was ist eine Hookline?", "Akkordfolgen.", "Refrain schreiben."],
                    "responses": ["Um einen Song zu schreiben, beginne mit einer Idee oder Melodie.", "Eine Hookline ist ein einpraegsamer Teil eines Songs.", "Texten erfordert Kreativitaet und Uebung.", "Melodien sind das Herzstueck vieler Songs."]
                },
                "musikindustrie": {
                    "patterns": ["Wie funktioniert die Musikindustrie?", "Rolle von Plattenfirmen.", "Was ist GEMA?", "Wie verdiene ich Geld mit Musik?", "Musikstreaming.", "Urheberrecht in der Musik."],
                    "responses": ["Die Musikindustrie umfasst Produktion, Vertrieb und Marketing.", "Plattenfirmen unterstuetzen Kuenstler.", "Die GEMA ist eine Verwertungsgesellschaft fuer musikalische Urheberrechte.", "Geld mit Musik kann man durch [Wege] verdienen."]
                }
            }
        },
        "literaturproduktion": {
            "description": "Fragen zum Schreiben von Buechern und Texten.",
            "sub_topics": {
                "buch_schreiben": {
                    "patterns": ["Wie schreibe ich ein Buch?", "Tipps fuer Romanautoren.", "Charakterentwicklung.", "Plot entwickeln.", "Schreibblockade ueberwinden.", "Einen Bestseller schreiben."],
                    "responses": ["Ein Buch zu schreiben erfordert Planung und Disziplin.", "Charakterentwicklung ist wichtig fuer glaubwuerdige Figuren.", "Ein Plot ist die Handlung eines Buches.", "Schreibblockaden sind normal, aber ueberwindbar."]
                },
                "genres_erklaerung": {
                    "patterns": ["Was ist Fantasy-Literatur?", "Merkmale von Science-Fiction.", "Erklaere Kriminalromane.", "Was ist eine Novelle?", "Thriller Merkmale.", "Historische Romane."],
                    "responses": ["Fantasy-Literatur entfuehrt in magische Welten.", "Science-Fiction befasst sich mit Zukunftstechnologien.", "Ein Kriminalroman handelt von einem Verbrechen.", "Eine Novelle ist eine kurze Erzaehlung."]
                },
                "veroeffentlichung": {
                    "patterns": ["Wie veroeffentliche ich ein Buch?", "Self-Publishing erklaeren.", "Verlag finden.", "Marketing fuer Autoren.", "E-Book veroeffentlichen.", "Buchcover gestalten."],
                    "responses": ["Ein Buch zu veroeffentlichen kann ueber Verlage oder Self-Publishing erfolgen.", "Self-Publishing bietet Kontrolle ueber den Prozess.", "Einen Verlag findest du durch [Wege].", "Buchmarketing ist wichtig fuer den Erfolg."]
                },
                "poesie": {
                    "patterns": ["Wie schreibt man ein Gedicht?", "Arten von Gedichten.", "Reime finden.", "Was ist Metapher in der Poesie?", "Haiku erklaeren.", "Lyrik verstehen."],
                    "responses": ["Ein Gedicht zu schreiben, erfordert Kreativitaet.", "Es gibt verschiedene Arten von Gedichten wie Sonette oder Haikus.", "Metaphern sind Stilmittel in der Poesie.", "Reime sind Klanggleichheiten am Ende von Versen."]
                }
            }
        }
    }
    
    generated_patterns_count = 0
    generated_responses_count = 0

    # Allgemeine Platzhalter fuer flexiblere Generierung
    common_placeholders = {
        "{ort}": ["Berlin", "Muenchen", "Hamburg", "Koeln", "Frankfurt", "Stuttgart", "Dresden", "Leipzig", "Bremen", "Hannover", "Dortmund", "Duesseldorf", "Luedenscheid", "New York", "London", "Paris", "Rom", "Tokio", "Sydney", "Wien", "Zuerich", "Amsterdam", "Madrid", "Peking", "Kairo", "Rio de Janeiro", "Kapstadt", "Dubai", "Moskau"],
        "{person}": ["Albert Einstein", "Marie Curie", "Leonardo da Vinci", "William Shakespeare", "Angela Merkel", "Nelson Mandela", "Elon Musk", "Steve Jobs", "Bjoern Hoecke", "Konrad Adenauer", "Helmut Schmidt", "Stephen Hawking", "Isaac Newton", "Charles Darwin", "Leonardo DiCaprio", "Meryl Streep", "Michael Jackson", "Wolfgang Amadeus Mozart", "Johann Sebastian Bach", "Friedrich Schiller", "Johann Wolfgang von Goethe", "Immanuel Kant"],
        "{thema}": ["Klimawandel", "kuenstliche Intelligenz", "Quantenphysik", "Geschichte des Internets", "gesunde Ernaehrung", "nachhaltige Entwicklung", "finanzielle Freiheit", "Astrophysik", "Robotik", "Genetik", "Philosophie des Geistes", "moderne Kunst", "digitale Transformation", "Big Data", "Blockchain-Technologie"],
        "{land}": ["Deutschland", "Frankreich", "USA", "China", "Indien", "Japan", "Kanada", "Australien", "Spanien", "Italien", "Grossbritannien", "Russland", "Brasilien", "Suedafrika", "Aegypten", "Mexiko", "Argentinien", "Schweden", "Norwegen", "Daenemark"],
        "{zeit}": ["morgen", "naechste Woche", "im Sommer", "im Winter", "in den Ferien", "bald", "am Wochenende", "heute Abend", "naechsten Monat", "im Fruehling", "im Herbst"],
        "{produkt}": ["Smartphone", "Laptop", "Smartwatch", "Kopfhoerer", "Kamera", "Fitness-Tracker", "E-Bike", "Tablet", "VR-Brille", "Drohne", "smarter Lautsprecher", "Gaming-Konsole", "robotischer Staubsauger"],
        "{sportart}": ["Fussball", "Basketball", "Tennis", "Schwimmen", "Eishockey", "Golf", "Boxen", "Handball", "Volleyball", "Leichtathletik", "Ski alpin", "Snowboarden", "Badminton", "Tischtennis", "Formel 1", "E-Sport"],
        "{krankheit}": ["Grippe", "Diabetes", "Bluthochdruck", "Krebs", "Depression", "Allergie", "Alzheimer", "Parkinson", "Herzinfarkt", "Schlaganfall", "Asthma", "Migraene"],
        "{sprache}": ["Englisch", "Spanisch", "Franzoesisch", "Chinesisch", "Deutsch", "Italienisch", "Russisch", "Arabisch", "Japanisch", "Koreanisch", "Portugiesisch"],
        "{gericht}": ["Lasagne", "Pizza", "Sushi", "Currywurst", "Burger", "Spaghetti Carbonara", "Paella", "Tacos", "Curry", "Pho", "Ramen", "Fish and Chips", "Wiener Schnitzel"],
        "{app}": ["Spotify", "WhatsApp", "Instagram", "Facebook", "TikTok", "YouTube", "Twitter", "Telegram", "Discord", "Zoom", "Netflix", "Google Maps"],
        "{geraet}": ["Smart-TV", "Staubsaugerroboter", "Thermostat", "Ueberwachungskamera", "smartes Licht", "intelligenter Kuehlschrank", "Sprachassistent", "smarte Steckdose"],
        "{ereignis}": ["Zweiter Weltkrieg", "franzoesische Revolution", "Mondlandung", "Fall der Berliner Mauer", "Olympiade {jahr}", "industrielle Revolution", "Entdeckung Amerikas", "Kalte Krieg", "11. September", "Tschernobyl"],
        "{jahr}": ["1945", "1789", "1989", "2001", "1492", "1969", "1914", "1939", "1961"],
        "{konzept}": ["Relativitaetstheorie", "Photosynthese", "Blockchain", "Quantenverschraenkung", "Demokratie", "Kapitalismus", "Sozialismus", "Feminismus", "Existenzialismus", "Utilitarismus", "Thermodynamik", "Genetik"],
        "{programmiersprache}": ["Python", "Java", "C++", "JavaScript", "Rust", "Go", "Swift", "C#", "PHP", "Ruby", "Kotlin", "TypeScript"],
        "{beruf}": ["Lehrer", "Arzt", "Programmierer", "Ingenieur", "Kuenstler", "Pilot", "Anwalt", "Architekt", "Wissenschaftler", "Journalist", "Unternehmer", "Designer"],
        "{buch}": ["Herr der Ringe", "1984", "Faust", "Die Bibel", "Der kleine Prinz", "Harry Potter", "Krieg und Frieden", "Moby Dick", "Stolz und Vorurteil", "Der Faenger im Roggen"],
        "{film}": ["Inception", "Matrix", "Der Pate", "Forrest Gump", "Star Wars", "Avatar", "Der Herr der Ringe", "Pulp Fiction", "Titanic", "Fight Club", "Interstellar"]
    }

    def replace_placeholders(text):
        """Ersetzt Platzhalter in einem Text durch zufaellige Werte."""
        for ph, values in common_placeholders.items():
            if ph in text:
                text = text.replace(ph, random.choice(values))
        return text

    # Liste, um alle zu inserierenden Intents zu sammeln (fuer Bulk-Insert)
    intents_to_bulk_insert = []

    for main_topic_tag, main_topic_data in topics_data.items():
        main_topic_description = main_topic_data["description"]
        for sub_topic_tag, sub_topic_data in main_topic_data["sub_topics"].items():
            
            tag = f"{main_topic_tag}_{sub_topic_tag}"
            description = f"{main_topic_description} Spezifisch zu {sub_topic_tag.replace('_', ' ')}."
            
            current_intent_patterns = []
            current_intent_responses = []

            # Fuege Basis-Patterns und Responses hinzu (mit Platzhalterersetzung)
            for p_text in sub_topic_data["patterns"]:
                current_intent_patterns.append(replace_placeholders(p_text))
                generated_patterns_count += 1
            for r_text in sub_topic_data["responses"]:
                current_intent_responses.append(replace_placeholders(r_text))
                generated_responses_count += 1

            # Generiere ZUSAETZLICHE Variationen
            num_extra_variations_per_base = random.randint(30, 50) 

            for _ in range(num_extra_variations_per_base):
                if sub_topic_data["patterns"]:
                    chosen_pattern = random.choice(sub_topic_data["patterns"])
                    
                    variation_type = random.choice(["question_prefix", "command_suffix", "rephrase", "detailed_question", "casual_question", "negative_form", "synonym_replace", "imperative", "alternative_verb", "passive_voice", "simple_statement"])
                    
                    new_pattern = chosen_pattern

                    if variation_type == "question_prefix":
                        prefixes = ["Kannst du mir sagen,", "Ich moechte wissen,", "Erzaehl mir bitte,", "Hast du Infos zu", "Weisst du etwas ueber", "Gib mir Informationen zu", "Koenntest du mir erklaeren,", "Was ist mit", "Inwiefern ist"]
                        if "?" not in new_pattern and "." not in new_pattern:
                            new_pattern = f"{random.choice(prefixes)} {new_pattern.lower()}?"
                        else:
                            new_pattern = f"{random.choice(prefixes)} {new_pattern.lower().replace('?', '').replace('.', '')}."
                    elif variation_type == "command_suffix":
                        if "bitte" not in new_pattern.lower():
                            suffixes = ["bitte.", "mal.", "jetzt.", "sofort.", "kurz.", "schnell."]
                            new_pattern = new_pattern.replace("?", "").replace(".", "") + f" {random.choice(suffixes)}"
                        else:
                            new_pattern = new_pattern
                    elif variation_type == "rephrase":
                        rephrases = ["Wie steht es um {text}?", "Infos zu {text}.", "Was gibt es Neues bezueglich {text}?", "Kannst du mir {text} naeher bringen?", "Erzaehl' mir doch mal etwas ueber {text}.", "Ueber {text} bitte.", "Kannst du {text} beschreiben?"]
                        new_pattern = random.choice(rephrases).format(text=new_pattern.lower().replace('?', '').replace('.', ''))
                    elif variation_type == "detailed_question":
                        new_pattern = f"Kannst du mir mehr Details zu {new_pattern.lower().replace('?', '').replace('.', '')} geben?"
                    elif variation_type == "casual_question":
                         new_pattern = f"Sag mal, was ist eigentlich mit {new_pattern.lower().replace('?', '').replace('.', '')}?"
                    elif variation_type == "negative_form":
                        negations = {"ist": "ist nicht", "hat": "hat nicht", "sind": "sind nicht", "kann": "kann nicht", "wird": "wird nicht"}
                        found_negation = False
                        for key, value in negations.items():
                            if key in new_pattern.lower():
                                new_pattern = new_pattern.lower().replace(key, value, 1) # Nur das erste Vorkommen ersetzen
                                found_negation = True
                                break
                        if not found_negation: # Wenn keine direkte Negation moeglich, einfach praefix
                            new_pattern = f"Ist es nicht so, dass {new_pattern.lower().replace('?', '').replace('.', '')}?"
                    elif variation_type == "synonym_replace":
                        synonyms = {
                            "gut": ["toll", "schoen", "super", "klasse", "prima", "ausgezeichnet"],
                            "schlecht": ["mies", "schlimm", "furchtbar", "grauenhaft", "katastrophal", "aergerlich"],
                            "gross": ["riesig", "enorm", "gewaltig", "umfangreich", "betraechtlich", "umfassend"],
                            "klein": ["winzig", "minimal", "niedlich", "gering", "mikroskopisch", "kurz"],
                            "sagen": ["erzaehlen", "berichten", "mitteilen", "informieren", "aeussern"],
                            "fragen": ["erkundigen", "erfragen", "wissen wollen", "nachhaken"],
                            "machen": ["tun", "erstellen", "fertigen", "produzieren", "durchfuehren", "bewirken"]
                        }
                        words_in_pattern = new_pattern.split()
                        for i, word in enumerate(words_in_pattern):
                            lower_word = word.lower().strip(".,?!")
                            if lower_word in synonyms:
                                words_in_pattern[i] = random.choice(synonyms[lower_word])
                                if word.isupper(): words_in_pattern[i] = words_in_pattern[i].upper()
                                elif word[0].isupper(): words_in_pattern[i] = words_in_pattern[i].capitalize()
                        new_pattern = " ".join(words_in_pattern)
                    elif variation_type == "imperative":
                        if "?" in new_pattern:
                            new_pattern = new_pattern.replace("?", "").replace("Wie ist", "Nenne mir").replace("Was ist", "Definiere").replace("Wer ist", "Beschreibe")
                        else:
                            new_pattern = f"Nenne mir {new_pattern.lower()}."
                    elif variation_type == "alternative_verb":
                        verbs_replace = {"erklaere": ["beschreibe", "definiere", "erlaeutere"], "was ist": ["was bedeutet", "was umfasst"], "wie funktioniert": ["erklaere die Funktion von", "wie laeuft"], "kannst du": ["bitte", "moechtest du"]}
                        for original_verb, alternatives in verbs_replace.items():
                            if original_verb in new_pattern.lower():
                                new_pattern = new_pattern.lower().replace(original_verb, random.choice(alternatives), 1)
                                break
                    elif variation_type == "passive_voice":
                        # Sehr rudimentaere Passiv-Form (braucht NLTK fuer komplexere Faelle)
                        if "ist" in new_pattern.lower() and "wird" not in new_pattern.lower():
                            new_pattern = new_pattern.lower().replace("ist", "wird", 1) + " gemacht?" # nur Beispiel
                        else:
                            new_pattern = new_pattern # Fallback
                    elif variation_type == "simple_statement":
                        new_pattern = new_pattern.replace("?", "").replace(".", "") + "."


                    # Zusaetzliche grammatikalische Variationen (bleiben bestehen)
                    new_pattern = new_pattern.replace("Wie ist", "Kannst du mir sagen, wie es um")
                    new_pattern = new_pattern.replace("Was ist", "Ich brauche eine Erklaerung fuer")
                    new_pattern = new_pattern.replace("Wer ist", "Alle Infos zu")
                    new_pattern = new_pattern.replace("Wann ist", "Kannst du das Datum von")
                    new_pattern = new_pattern.replace("Regeln fuer", "Wie sind die Regeln fuer")
                    
                    current_intent_patterns.append(replace_placeholders(new_pattern))
                    generated_patterns_count += 1
                
                if sub_topic_data["responses"]:
                    chosen_response = random.choice(sub_topic_data["responses"])
                    
                    response_type = random.choice(["simple", "elaborate", "affirmative", "question_prompt", "summary", "short_detail", "example_add", "direct_answer", "reassurance", "conditional_response", "opinion_like"])
                    new_response = chosen_response

                    if response_type == "elaborate":
                        elaboration_phrases = ["Des Weiteren ist zu beachten,", "Dazu kommt noch, dass", "Wichtig hierbei ist,", "Zusaetzlich kann man sagen, dass", "Ein weiterer Aspekt ist", "Es ist erwaehnenswert, dass", "Ausserdem ist es wichtig zu wissen, dass"]
                        new_response = f"{chosen_response} {random.choice(elaboration_phrases)} [weitere generische Info]."
                    elif response_type == "affirmative":
                        affirmations = ["Gerne.", "Absolut.", "Ja, sicher.", "Verstanden.", "Einverstanden.", "Kein Problem.", "Ja, selbstverstaendlich.", "Bestens."]
                        new_response = f"{random.choice(affirmations)} {chosen_response}"
                    elif response_type == "question_prompt":
                        question_prompts = ["Moechtest du mehr darueber wissen?", "Kann ich dir noch weitere Details geben?", "Was interessiert dich noch zu diesem Thema?", "Brauchst du weitere Informationen?", "Soll ich tiefer ins Detail gehen?", "Gibt es noch etwas, das ich erklaeren kann?"]
                        new_response = f"{chosen_response} {random.choice(question_prompts)}"
                    elif response_type == "summary":
                        summaries = ["Kurz gesagt,", "Zusammenfassend laesst sich sagen,", "In Summe bedeutet das, dass", "Zusammenfassend lautet die Antwort:", "Die Quintessenz ist:", "Das Wichtigste ist:"]
                        new_response = f"{random.choice(summaries)} {chosen_response.lower().replace('.', '')}."
                    elif response_type == "short_detail":
                        short_details = ["Das ist ein wichtiger Punkt.", "Es ist bekannt, dass...", "Man kann davon ausgehen, dass...", "Fakt ist, dass...", "Interessanterweise ist..."]
                        new_response = f"{random.choice(short_details)} {chosen_response.lower()}"
                    elif response_type == "example_add":
                        example_phrases = ["Ein Beispiel dafuer ist:", "Man koennte es vergleichen mit:", "Stell dir vor:", "Das laesst sich am Beispiel von [Beispiel] verdeutlichen.", "Nimm zum Beispiel:"]
                        new_response = f"{chosen_response} {random.choice(example_phrases)} [generisches Beispiel]."
                    elif response_type == "direct_answer":
                        new_response = chosen_response.replace(".", "") + "." # Stellt sicher, dass es ein einfacher, direkter Satz ist
                    elif response_type == "reassurance":
                        reassurances = ["Das ist eine sehr gute Frage.", "Ein wichtiges Thema.", "Ich helfe dir gerne dabei.", "Ich verstehe deine Frage."]
                        new_response = f"{random.choice(reassurances)} {chosen_response}"
                    elif response_type == "conditional_response":
                        conditionals = ["Wenn du [Bedingung] bedenkst, dann [Erklaerung].", "Unter der Voraussetzung, dass [Voraussetzung], dann [Erklaerung]."]
                        new_response = f"{chosen_response} {random.choice(conditionals)}"
                    elif response_type == "opinion_like":
                        opinions = ["Ich persoenlich finde, dass...", "Es wird oft angenommen, dass...", "Viele Experten sind der Meinung, dass..."]
                        new_response = f"{random.choice(opinions)} {chosen_response.lower().replace('.', '')}."

                    current_intent_responses.append(replace_placeholders(new_response))
                    generated_responses_count += 1
            
            # Fuege den gesamten Intent mit allen generierten Patterns und Responses zur Bulk-Liste hinzu
            intents_to_bulk_insert.append({
                "tag": tag,
                "description": description,
                "patterns": current_intent_patterns,
                "responses": current_intent_responses
            })

    # Bulk-Insert in MongoDB, um Performance zu optimieren
    if intents_to_bulk_insert:
        try:
            collection.insert_many(intents_to_bulk_insert)
            print(f"  {len(intents_to_bulk_insert)} generierte Intents in MongoDB eingefuegt.")
        except pymongo.errors.BulkWriteError as e:
            print(f"  Fehler beim Bulk-Insert in MongoDB: {e.details}")
        except Exception as e:
            print(f"  Unerwarteter Fehler beim Bulk-Insert: {e}")

    print(f"\nGenerierung abgeschlossen. Es wurden folgende Daten erstellt:")
    print(f"  Gesamtanzahl der generierten Patterns: {generated_patterns_count}")
    print(f"  Gesamtanzahl der generierten Responses: {generated_responses_count}")
    print(f"  Gesamt-Eintraege in 'patterns_and_responses' Tabelle (geschaetzt): {generated_patterns_count + generated_responses_count}")


def main():
    collection = get_mongo_collection()
    # KORRIGIERTE ZEILE: Explizite Pruefung auf None
    if collection is not None: 
        # Loesche alle vorhandenen Dokumente in der Collection fuer einen sauberen Start
        collection.delete_many({})
        print(f"Vorherige Daten in MongoDB Collection '{COLLECTION_NAME}' geloescht.")

        script_dir = os.path.dirname(__file__)
        # Zuerst die initiale JSON laden
        populate_db_from_json(collection, os.path.join(script_dir, INITIAL_INTENTS_FILE))
        
        # Dann die umfangreichen Intents generieren
        generate_extensive_intents(collection)
        
        # MongoDB-Client muss nicht explizit geschlossen werden, PyMongo handhabt das
        print(f"\nMongoDB Collection '{COLLECTION_NAME}' erfolgreich befuellt.")
    else: # Fallback, falls get_mongo_collection aus irgendeinem Grund None zurueckgibt (unwahrscheinlich mit sys.exit)
        print("MongoDB-Collection konnte nicht abgerufen werden. Abbruch.")

if __name__ == '__main__':
    print(f"Startzeit des Datenbank-Setups: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    main()
    print(f"Endzeit des Datenbank-Setups: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n---------------------------------------")
    print("Das Datenbank-Setup-Programm ist beendet. Druecke eine beliebige Taste, um das Fenster zu schliessen...")
    if sys.stdin.isatty():
        input()
    else:
        pass