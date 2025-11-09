# -*- coding: utf-8 -*-
# // -- Peter Luebke Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.

import os
import importlib.util
import inspect
import sys
import logging

class PluginManager:
    def __init__(self, plugin_folder: str, logic_controller):
        """
        Initialisiert den PluginManager.
        :param plugin_folder: Der Pfad zum Ordner, der die Plugin-Dateien enthält.
        :param logic_controller: Eine Referenz auf die CaliaLogic-Instanz.
        """
        self.plugin_folder = plugin_folder
        self.logic = logic_controller  # Speichere die Referenz auf die Hauptlogik
        self.commands = {}
        self.plugin_instances = {}

        if plugin_folder not in sys.path:
            sys.path.append(plugin_folder)

    def load_plugins(self):
        """
        Scannt den Plugin-Ordner, lädt alle Python-Module dynamisch
        und instanziiert Plugin-Klassen, um deren Befehle zu registrieren.
        """
        logging.info(f"Lade Plugins aus: {self.plugin_folder}")
        if not os.path.isdir(self.plugin_folder):
            logging.warning(f"Plugin-Verzeichnis '{self.plugin_folder}' nicht gefunden.")
            return

        for filename in os.listdir(self.plugin_folder):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]
                try:
                    # Dynamisches Laden des Moduls
                    module_path = os.path.join(self.plugin_folder, filename)
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    # Füge das Modul zu sys.modules hinzu, damit es von anderen Modulen gefunden werden kann
                    sys.modules[f"plugins.{module_name}"] = module
                    spec.loader.exec_module(module)

                    # Finde und instanziiere Plugin-Klassen (wie in deiner Original-Logik)
                    for attribute_name in dir(module):
                        attribute = getattr(module, attribute_name)
                        if inspect.isclass(attribute) and attribute_name.endswith("Plugin") and attribute.__module__ == module_name:
                            # Instanziiere das Plugin und übergebe die CaliaLogic-Referenz
                            plugin_instance = attribute(self.logic)
                            self.plugin_instances[attribute_name] = plugin_instance

                            # Registriere die "tools" oder Befehle des Plugins
                            # Wir gehen davon aus, dass die Instanz eine Methode 'register' oder Eigenschaft 'tools' hat
                            if hasattr(plugin_instance, 'register') and callable(getattr(plugin_instance, 'register')):
                                registered_tools = plugin_instance.register()
                                self.commands.update(registered_tools)
                                logging.info(f"Plugin '{attribute_name}' geladen mit Werkzeugen: {list(registered_tools.keys())}")

                except Exception as e:
                    logging.error(f"Fehler beim Laden des Plugins {module_name}: {e}", exc_info=True)

        logging.info(f"Insgesamt {len(self.commands)} Befehle geladen.")

    def execute_command(self, command_name: str, *args, **kwargs):
        """
        Führt einen zuvor geladenen Befehl aus.
        """
        command_func = self.commands.get(command_name)
        if command_func and callable(command_func):
            try:
                logging.info(f"Führe Befehl aus: {command_name}")
                return command_func(*args, **kwargs)
            except Exception as e:
                logging.error(f"Fehler bei der Ausführung von Befehl '{command_name}': {e}", exc_info=True)
                return f"Entschuldigung, es gab einen Fehler bei der Ausführung von {command_name}."
        else:
            # Wichtig: Gebe None zurück, damit die Hauptlogik weiß, dass kein Befehl gefunden wurde
            return None