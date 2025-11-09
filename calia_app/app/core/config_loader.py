# -*- coding: utf-8 -*-
# // -- Peter Luebke Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: Calia AI.
#
# core/config_loader.py
#
# Diese Datei bündelt alle Hilfsfunktionen für Konfiguration,
# Pfad-Management und Logging an einem zentralen Ort (SRP).

import os
import sys
import datetime
import logging
import json

# --- Versions- & Pfad-Konstanten ---

# Wir definieren das Basisverzeichnis der App (das Verzeichnis ÜBER 'core')
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

VERSION = "0.9.32-Refactored" 

# --- TensorFlow/CPU-Steuerung ---

def force_tensorflow_cpu():
    """Stellt sicher, dass TensorFlow nur die CPU nutzt."""
    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    print("[CALIA-INFO] TensorFlow wird explizit im CPU-Modus ausgeführt.")

# --- Pfad-Management ---

def get_resource_path(relative_path):
    """
    Ermittelt den korrekten Pfad zu einer Ressource, egal ob
    als Skript oder als kompilierte .exe (via PyInstaller) ausgeführt.
    """
    try:
        # PyInstaller erstellt ein temporäres Verzeichnis
        base_path = sys._MEIPASS
    except Exception:
        # Im normalen Skript-Modus ist es das definierte BASE_DIR
        base_path = BASE_DIR
    return os.path.join(base_path, relative_path)

# --- Logging-Setup ---

def setup_logging():
    """Initialisiert das globale Logging-System."""
    try:
        # Nutzt get_resource_path, um den data/logs-Ordner zu finden
        log_dir = get_resource_path(os.path.join('data', 'logs'))
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = os.path.join(log_dir, f"calia_log_{timestamp}.log")
        
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        if logger.hasHandlers(): logger.handlers.clear()
        
        # File Handler
        file_handler = logging.FileHandler(log_file, 'w', 'utf-8')
        file_formatter = logging.Formatter(
            f'%(asctime)s - V{VERSION} - %(levelname)-8s - %(module)s.%(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter('[DIAGNOSE] %(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
        
        logging.info(f"Logging-System initialisiert. Logs in: '{log_file}'")
    except Exception as e:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.critical(f"Konnte benutzerdefiniertes Logging nicht einrichten: {e}", exc_info=True)

# --- Config-Laden ---

def load_config():
    """Lädt die zentrale config.json."""
    config_path = get_resource_path("config.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.critical(f"FATAL: Konnte config.json nicht laden: {e}", exc_info=True)
        sys.exit()
