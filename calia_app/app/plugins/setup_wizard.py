# -*- coding: utf-8 -*-
# // -- Okami Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.

import pygame
import os
import json
import sqlite3
import logging
import requests
import tzdata

# Wir importieren genai hier, um Abhängigkeiten zu prüfen
try:
    import google.generativeai as genai
except ImportError:
    genai = None

class SetupWizard:
    """
    Eine eigenständige, Pygame-basierte GUI zur Ersteinrichtung von Calia.
    Enthält UX-Verbesserungen und API-Key-Validierung.
    """
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 500))
        pygame.scrap.init()
        pygame.display.set_caption("Calia - Einrichtungs-Assistent")
        self.clock = pygame.time.Clock()

        # Farben und Schriftarten
        self.BG_COLOR = (15, 20, 40)
        self.PRIMARY_COLOR = (0, 255, 255)
        self.SECONDARY_COLOR = (200, 255, 255)
        self.INPUT_BG_COLOR = (30, 40, 60)
        self.DISABLED_COLOR = (100, 100, 100)
        self.SUCCESS_COLOR = (0, 200, 0)
        self.ERROR_COLOR = (200, 0, 0)
        self.font_title = pygame.font.SysFont("Segoe UI Light", 40)
        self.font_text = pygame.font.SysFont("Segoe UI", 22)
        self.font_input = pygame.font.SysFont("Consolas", 20)
        self.font_icon = pygame.font.SysFont("Segoe UI Emoji", 20)

        # Assistenten-Logik
        self.current_step = 0
        self.active_input_index = 0
        self.key_status = {}
        self.common_timezones = [
            "Europe/Berlin", "Europe/London", "Europe/Paris", "UTC",
            "America/New_York", "America/Los_Angeles", "Asia/Tokyo", "Australia/Sydney"
        ]
        self.printed_tz_info = False
        self.steps = [
            {"title": "Willkommen bei Calia!", "fields": [], "button": "Starten"},
            {"title": "API-Schlüssel: Google Gemini", "fields": [{"key": "GEMINI_API_KEY", "label": "Gemini Key:", "value": ""}], "button": "Weiter"},
            {"title": "API-Schlüssel: Weitere Dienste", "fields": [{"key": "OPENWEATHERMAP_API_KEY", "label": "OpenWeatherMap Key:", "value": ""}, {"key": "NEWS_API_KEY", "label": "NewsAPI Key:", "value": ""}], "button": "Weiter"},
            {"title": "Benutzerprofil", "fields": [
                {"key": "user_name", "label": "Dein Name:", "value": ""},
                {"key": "user_location", "label": "Dein Wohnort:", "value": ""},
                {"key": "user_timezone", "label": "Deine Zeitzone (Nr.):", "value": "1"}
            ], "button": "Speichern & Starten"},
        ]

    def _is_step_valid(self):
        """Prüft, ob alle Bedingungen für den aktuellen Schritt erfüllt sind."""
        step_info = self.steps[self.current_step]
        if step_info['title'] == "Willkommen bei Calia!":
            return True # Erster Schritt ist immer gültig
        
        for field in step_info['fields']:
            if "API_KEY" in field['key']:
                if self.key_status.get(field['key']) != 'ok':
                    return False
        
        if step_info['title'] == "Benutzerprofil":
            if not any(f['value'] for f in step_info['fields'] if f['key'] == 'user_name'):
                return False
        return True

    def _test_api_key(self, field_key, api_key):
        """Testet einen API-Schlüssel und aktualisiert den Status."""
        self.key_status[field_key] = 'testing'
        self._draw()
        
        try:
            if field_key == "GEMINI_API_KEY":
                if not genai: raise ImportError("Gemini-Bibliothek nicht gefunden.")
                if not api_key: raise ValueError("API-Schlüssel ist leer.")
                genai.configure(api_key=api_key)
                next(genai.list_models())
            elif field_key == "OPENWEATHERMAP_API_KEY":
                if not api_key: raise ValueError("API-Schlüssel ist leer.")
                res = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q=London&appid={api_key}")
                if res.status_code != 200: raise ValueError(f"API-Fehler: {res.json().get('message', 'Unbekannt')}")
            elif field_key == "NEWS_API_KEY":
                if not api_key: raise ValueError("API-Schlüssel ist leer.")
                res = requests.get(f"https://newsapi.org/v2/top-headlines?country=de&apiKey={api_key}")
                if res.status_code != 200: raise ValueError(f"API-Fehler: {res.json().get('message', 'Unbekannt')}")
            
            self.key_status[field_key] = 'ok'
        except Exception as e:
            logging.warning(f"API-Key-Test für {field_key} fehlgeschlagen: {e}")
            self.key_status[field_key] = 'error'

    def run(self):
        """Die Hauptschleife des Einrichtungs-Assistenten."""
        running = True
        while running:
            if self.current_step >= len(self.steps):
                running = False
                continue

            step_info = self.steps[self.current_step]
            step_is_valid = self._is_step_valid()

            if step_info['title'] == "Benutzerprofil" and not self.printed_tz_info:
                print("\n--- Bitte wählen Sie Ihre Zeitzone ---")
                for i, tz in enumerate(self.common_timezones, 1):
                    print(f"{i}: {tz}")
                print("Geben Sie die entsprechende Nummer in das Feld ein.")
                self.printed_tz_info = True

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    return False # Wichtig: Signalisiert Abbruch

                if event.type == pygame.MOUSEBUTTONDOWN:
                    for i, field in enumerate(step_info['fields']):
                        input_rect = pygame.Rect(250, 150 + i * 60 - 5, 400, 40)
                        if input_rect.collidepoint(event.pos):
                            self.active_input_index = i
                        
                        if "API_KEY" in field['key']:
                            test_button_rect = pygame.Rect(input_rect.right + 10, input_rect.y, 80, 40)
                            if test_button_rect.collidepoint(event.pos):
                                self._test_api_key(field['key'], field['value'])

                    button_rect = pygame.Rect(300, 420, 200, 50)
                    if button_rect.collidepoint(event.pos) and step_is_valid:
                        self._next_step()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and step_is_valid:
                        self._next_step()
                        continue
                    
                    if self.active_input_index < len(step_info['fields']):
                        active_field = step_info['fields'][self.active_input_index]
                        if event.key == pygame.K_BACKSPACE:
                            active_field['value'] = active_field['value'][:-1]
                        elif event.key == pygame.K_v and (event.mod & pygame.KMOD_CTRL):
                            pasted_text = pygame.scrap.get(pygame.SCRAP_TEXT)
                            if pasted_text:
                                try:
                                    active_field['value'] += pasted_text.decode('utf-8').strip()
                                except (UnicodeDecodeError, AttributeError): pass
                        else:
                            if len(event.unicode) > 0 and ord(event.unicode) > 0 :
                                active_field['value'] += event.unicode
                        
                        if "API_KEY" in active_field['key']:
                           self.key_status.pop(active_field['key'], None)

            self._draw()
            self.clock.tick(60)
        
        return True
    
    def _next_step(self):
        """Geht zum nächsten Schritt oder beendet den Wizard."""
        self.current_step += 1
        self.active_input_index = 0
        self.printed_tz_info = False
        if self.current_step >= len(self.steps):
            self._save_config()

    def _draw(self):
        """Zeichnet die GUI für den aktuellen Schritt."""
        self.screen.fill(self.BG_COLOR)
        if self.current_step >= len(self.steps): return
        
        step_info = self.steps[self.current_step]
        step_is_valid = self._is_step_valid()

        title_surf = self.font_title.render(step_info['title'], True, self.PRIMARY_COLOR)
        self.screen.blit(title_surf, title_surf.get_rect(center=(400, 60)))
        
        y_offset = 150
        for i, field in enumerate(step_info['fields']):
            label_surf = self.font_text.render(field['label'], True, self.SECONDARY_COLOR)
            self.screen.blit(label_surf, (50, y_offset))
            
            input_rect = pygame.Rect(250, y_offset - 5, 400, 40)
            pygame.draw.rect(self.screen, self.INPUT_BG_COLOR, input_rect)
            border_color = self.PRIMARY_COLOR if i == self.active_input_index else self.INPUT_BG_COLOR
            pygame.draw.rect(self.screen, border_color, input_rect, 2)
            
            value_surf = self.font_input.render(field['value'], True, self.SECONDARY_COLOR)
            self.screen.blit(value_surf, (input_rect.x + 10, input_rect.y + 10))

            if "API_KEY" in field['key']:
                test_button_rect = pygame.Rect(input_rect.right + 10, input_rect.y, 80, 40)
                pygame.draw.rect(self.screen, self.PRIMARY_COLOR, test_button_rect)
                test_text_surf = self.font_text.render("Test", True, self.BG_COLOR)
                self.screen.blit(test_text_surf, test_text_surf.get_rect(center=test_button_rect.center))

                status = self.key_status.get(field['key'])
                status_icon = ""
                status_color = self.SECONDARY_COLOR
                if status == 'ok':
                    status_icon = "✅"
                    status_color = self.SUCCESS_COLOR
                elif status == 'error':
                    status_icon = "❌"
                    status_color = self.ERROR_COLOR
                elif status == 'testing':
                    status_icon = "..."
                
                status_surf = self.font_icon.render(status_icon, True, status_color)
                self.screen.blit(status_surf, (test_button_rect.right + 10, test_button_rect.centery - 10))
            y_offset += 60

        button_rect = pygame.Rect(300, 420, 200, 50)
        button_color = self.PRIMARY_COLOR if step_is_valid else self.DISABLED_COLOR
        pygame.draw.rect(self.screen, button_color, button_rect)
        
        button_text = step_info.get("button", "Weiter")
        button_surf = self.font_text.render(button_text, True, self.BG_COLOR)
        self.screen.blit(button_surf, button_surf.get_rect(center=button_rect.center))
        
        pygame.display.flip()

    def _save_config(self):
        """
        Sammelt die Daten und speichert sie:
        - API-Schlüssel werden in die .env-Datei geschrieben.
        - Benutzerprofil-Daten werden in die Datenbank geschrieben.
        """
        logging.info("Speichere Konfiguration aus dem Einrichtungs-Assistenten...")
        
        # 1. Alle Daten aus den Wizard-Schritten sammeln
        temp_data = {}
        for step in self.steps:
            for field in step['fields']:
                temp_data[field['key']] = field['value']

        # 2. API-Schlüssel in die .env-Datei schreiben
        env_path = ".env"
        try:
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write("# Diese Datei wurde automatisch vom Calia Setup Wizard erstellt.\n")
                f.write("# API-Schlüssel für Google & Gemini\n")
                f.write(f'GEMINI_API_KEY="{temp_data.get("GEMINI_API_KEY", "")}"\n\n')
                
                f.write("# API-Schlüssel für weitere Dienste\n")
                f.write(f'OPENWEATHERMAP_API_KEY="{temp_data.get("OPENWEATHERMAP_API_KEY", "")}"\n')
                f.write(f'NEWS_API_KEY="{temp_data.get("NEWS_API_KEY", "")}"\n\n')
                
                # Fügen Sie hier Platzhalter für andere Schlüssel hinzu, die Calia benötigt
                f.write("# Weitere, vom Wizard nicht abgefragte Schlüssel (bei Bedarf manuell einfügen)\n")
                f.write('PICOWVOICE_ACCESS_KEY=""\n')
                f.write('OPENAI_API_KEY=""\n')
                f.write('GOOGLE_APPLICATION_CREDENTIALS="gcloud_credentials.json"\n')

            logging.info(f"API-Schlüssel erfolgreich in '{env_path}' gespeichert.")
        except Exception as e:
            logging.error(f"Fehler beim Schreiben der .env-Datei: {e}")

        # 3. Benutzerprofil in der Datenbank speichern (dieser Teil bleibt fast identisch)
        user_name = temp_data.get('user_name') or "User"
        user_location = temp_data.get('user_location') or "Lüdenscheid"
        user_timezone_str = "Europe/Berlin"
        
        try:
            tz_index = int(temp_data.get('user_timezone', 1)) - 1
            if 0 <= tz_index < len(self.common_timezones):
                user_timezone_str = self.common_timezones[tz_index]
        except (ValueError, TypeError):
            pass # Behält den Standardwert bei
            
        db_path = "calia.db"
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # Stellt sicher, dass die Tabelle existiert, bevor geschrieben wird.
            cursor.execute("CREATE TABLE IF NOT EXISTS user_profile (user_id TEXT PRIMARY KEY, name TEXT, location TEXT, facts TEXT, style_profile_cache TEXT, timezone TEXT)")
            
            cursor.execute("UPDATE user_profile SET name = ?, location = ?, timezone = ? WHERE user_id = 'default'", (user_name, user_location, user_timezone_str))
            if cursor.rowcount == 0:
                cursor.execute("INSERT INTO user_profile (user_id, name, location, facts, style_profile_cache, timezone) VALUES ('default', ?, ?, ?, ?, ?)", (user_name, user_location, '{}', None, user_timezone_str))
            
            conn.commit()
            conn.close()
            logging.info("Benutzerprofil in der Datenbank aktualisiert.")
        except Exception as e:
            logging.error(f"Fehler beim Aktualisieren der Datenbank: {e}")