# -*- coding: utf-8 -*-
# // -- Peter Luebke Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.


import os
import logging
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

try:
    import google.generativeai as genai
    from google.cloud import texttospeech
    from openai import OpenAI
except ImportError:
    genai, texttospeech, OpenAI = None, None, None

CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar']

class ServiceManager:
    def __init__(self, config: dict, script_dir: str):
        self.config = config
        self.script_dir = script_dir

    def init_gemini(self, tools: list, system_prompt_override: str = None):
        """
        Initialisiert und gibt den Gemini GenerativeModel Client zurück.
        Nimmt jetzt den system_prompt_override korrekt an.
        """
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not (genai and gemini_key):
            logging.warning("Gemini API-Schlüssel fehlt. Gemini-Dienst nicht verfügbar.")
            return None
        try:
            genai.configure(api_key=gemini_key)
            
            # KORREKTE LOGIK FÜR SYSTEM-PROMPT
            if system_prompt_override:
                model = genai.GenerativeModel(
                    'gemini-1.5-pro-latest', 
                    tools=tools,
                    system_instruction=system_prompt_override
                )
                logging.info(f"Spezialist 'Gemini' mit Persönlichkeits-Prompt und {len(tools)} Werkzeugen ist bereit.")
            else:
                # Standard-Initialisierung ohne spezifischen System-Prompt
                model = genai.GenerativeModel('gemini-1.5-pro-latest', tools=tools)
                logging.info(f"Spezialist 'Gemini' mit {len(tools)} Werkzeugen ist bereit.")
            
            return model
        except Exception as e:
            logging.error(f"Gemini-Initialisierungsfehler: {e}")
            return None

    def init_openai(self):
        openai_key = os.getenv("OPENAI_API_KEY")
        if not (OpenAI and openai_key and "DEIN" not in openai_key):
            logging.warning("OpenAI API-Schlüssel fehlt. OpenAI-Dienst nicht verfügbar.")
            return None
        try:
            client = OpenAI(api_key=openai_key)
            logging.info("Spezialist 'OpenAI' ist bereit.")
            return client
        except Exception as e:
            logging.error(f"OpenAI-Initialisierungsfehler: {e}")
            return None

    def init_perplexity(self):
        pplx_key = os.getenv("PERPLEXITY_API_KEY")
        if not (OpenAI and pplx_key and "DEIN" not in pplx_key):
            logging.warning("Perplexity API-Schlüssel fehlt. Perplexity-Dienst nicht verfügbar.")
            return None
        try:
            client = OpenAI(api_key=pplx_key, base_url="https://api.perplexity.ai")
            logging.info("Spezialist 'Perplexity' ist bereit.")
            return client
        except Exception as e:
            logging.error(f"Perplexity-Initialisierungsfehler: {e}")
            return None

    def init_google_tts(self):
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if texttospeech and creds_path and os.path.exists(creds_path):
            try:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
                client = texttospeech.TextToSpeechClient()
                logging.info("Google TTS-Dienst ist bereit.")
                return client
            except Exception as e:
                logging.error(f"Google TTS-Initialisierungsfehler: {e}")
        return None

    def init_calendar(self):
        creds = None
        token_path = os.path.join(self.script_dir, 'token.json')
        creds_path = os.path.join(self.script_dir, 'credentials.json')
        if not os.path.exists(creds_path):
            logging.warning("Google Calendar 'credentials.json' nicht gefunden. Kalender-Dienst nicht verfügbar.")
            return None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, CALENDAR_SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try: creds.refresh(Request())
                except Exception: creds = None
            if not creds:
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, CALENDAR_SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token: token.write(creds.to_json())
        try:
            service = build('calendar', 'v3', credentials=creds)
            logging.info("Google Kalender-Dienst erfolgreich verbunden.")
            return service
        except HttpError as error:
            logging.error(f'Fehler beim Erstellen des Kalender-Dienstes: {error}')
            return None