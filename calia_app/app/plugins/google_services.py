# -*- coding: utf-8 -*-
# // -- Okami Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.

import logging
import datetime
import dateparser

class GoogleServicesPlugin:
    def __init__(self, logic_controller):
        self.logic = logic_controller

    def register(self):
        return {
            "create_calendar_event": self.create_calendar_event,
            "get_calendar_events": self.get_calendar_events
        }

    def create_calendar_event(self, date_time_description: str, title: str, guests: list[str] = None):
        if not self.logic.calendar_service: return "Kalender-Dienst nicht verfügbar."
        
        # --- START ÄNDERUNG ---
        # Hole die Zeitzone aus dem Nutzerprofil, mit einem Fallback auf UTC.
        user_timezone = self.logic.user_profile.get('timezone', 'UTC')
        
        start_time = dateparser.parse(date_time_description, languages=['de'], settings={'PREFER_DATES_FROM': 'future', 'TIMEZONE': user_timezone})
        if not start_time: return f"Datum '{date_time_description}' nicht verstanden."
        
        event = {'summary': title, 
                 'start': {'dateTime': start_time.isoformat(), 'timeZone': user_timezone},
                 'end': {'dateTime': (start_time + datetime.timedelta(hours=1)).isoformat(), 'timeZone': user_timezone}}
        # --- ENDE ÄNDERUNG ---
        
        if guests and isinstance(guests, list):
            event['attendees'] = [{'email': email} for email in guests]
        try:
            created_event = self.logic.calendar_service.events().insert(calendarId='primary', body=event, sendNotifications=True).execute()
            response_text = f"Termin '{created_event.get('summary')}' eingetragen."
            if guests: response_text += " Einladungen wurden versendet."
            return response_text
        except Exception as e:
            return f"Fehler beim Erstellen des Termins: {e}"

   # NEU: Diese interne Methode gibt strukturierte Rohdaten zurück.
    def _get_raw_calendar_events(self, max_results: int = 5):
        if not self.logic.calendar_service:
            return []
        try:
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = self.logic.calendar_service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            return events_result.get('items', [])
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der rohen Kalenderdaten: {e}")
            return []

    # ALT (modifiziert): Diese Methode wird von der KI aufgerufen und formatiert die Daten schön.
    def get_calendar_events(self, max_results: int = 5):
        events = self._get_raw_calendar_events(max_results)
        if not events:
            return 'Für die nahe Zukunft stehen keine Termine im Kalender.'
        
        response_text = "Hier sind deine nächsten Termine: "
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            start_dt = dateparser.parse(start).astimezone()
            zeit_str = start_dt.strftime('%A, %d. %B um %H:%M Uhr') if 'T' in start else f"ganztägig am {start_dt.strftime('%A, den %d. %B')}"
            response_text += f"{zeit_str}: {event['summary']}. "
        return response_text
