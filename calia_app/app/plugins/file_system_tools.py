# -*- coding: utf-8 -*-
# // -- Okami Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.

import os
import sys
import subprocess
import logging

class FileSystemToolsPlugin:
    def __init__(self, logic_controller):
        self.logic = logic_controller

    def register(self):
        return {
            "list_files_in_directory": self.list_files_in_directory,
            "find_file": self.find_file,
            "open_path": self.open_path,
        }

    def list_files_in_directory(self, directory_path: str):
        try:
            expanded_path = os.path.expanduser(directory_path)
            if not os.path.isdir(expanded_path):
                return f"Fehler: Das Verzeichnis '{directory_path}' wurde nicht gefunden."
            items = os.listdir(expanded_path)
            if not items:
                return f"Das Verzeichnis '{directory_path}' ist leer."
            item_list = ", ".join(items[:10])
            response = f"Im Ordner '{directory_path}' befinden sich: {item_list}"
            if len(items) > 10:
                response += f" und {len(items) - 10} weitere."
            return response
        except Exception as e:
            return f"Ich konnte auf das Verzeichnis '{directory_path}' nicht zugreifen."

    def find_file(self, filename: str, search_directory: str = "~"):
        try:
            start_path = os.path.expanduser(search_directory)
            logging.info(f"Starte Dateisuche für '{filename}' in '{start_path}'...")
            found_files = []
            for root, dirs, files in os.walk(start_path):
                if filename in files:
                    found_files.append(os.path.join(root, filename))
            if not found_files:
                return f"Ich konnte die Datei '{filename}' im Verzeichnis '{search_directory}' nicht finden."
            return f"Ich habe die Datei '{filename}' hier gefunden: {', '.join(found_files)}"
        except Exception as e:
            return "Bei der Dateisuche ist ein Fehler aufgetreten."

    def open_path(self, path: str):
        try:
            expanded_path = os.path.expanduser(path)
            if not os.path.exists(expanded_path):
                return f"Fehler: Der Pfad '{path}' existiert nicht."
            logging.info(f"Öffne Pfad: '{expanded_path}'")
            if sys.platform == "win32":
                os.startfile(expanded_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", expanded_path])
            else:
                subprocess.run(["xdg-open", expanded_path])
            return f"Okay, ich habe '{os.path.basename(path)}' geöffnet."
        except Exception as e:
            return f"Ich konnte '{path}' leider nicht öffnen."
