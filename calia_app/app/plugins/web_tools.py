# -*- coding: utf-8 -*-
# // -- Okami Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.

import logging
import requests
import wikipedia
import datetime
import os # Importieren, um auf Umgebungsvariablen zuzugreifen

class WebToolsPlugin:
    def __init__(self, logic_controller):
        self.logic = logic_controller
        self.config = self.logic.config
        # Umgebungsvariablen hier laden für sauberen Code
        self.openweathermap_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        self.news_api_key = os.getenv("NEWS_API_KEY")
        self.google_cse_api_key = os.getenv("GOOGLE_CSE_API_KEY")
        self.google_cse_id = os.getenv("GOOGLE_CSE_ID")
        wikipedia.set_lang("de")

    def register(self):
        return {
            "get_weather_info": self.get_weather_info,
            "get_news": self.get_news,
            "search_wikipedia": self.search_wikipedia,
            "web_search": self.web_search
        }

    def get_weather_info(self, location: str, days_ahead: int = 0):
        self.logic.last_weather_icon_code = None
        if not self.openweathermap_api_key: return {"result": "OpenWeatherMap API-Schlüssel fehlt."}
        if not location: location = self.logic.user_profile.get('location', 'Lüdenscheid')
        try:
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={self.openweathermap_api_key}"
            geo_data = requests.get(geo_url, timeout=10).json()
            if not geo_data: return {"result": f"Ort '{location}' nicht gefunden."}
            lat, lon = geo_data[0]['lat'], geo_data[0]['lon']
            weather_url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly,alerts&appid={self.openweathermap_api_key}&units=metric&lang=de"
            weather_data = requests.get(weather_url, timeout=10).json()
            if days_ahead == 0:
                current_weather = weather_data['current']
                self.logic.last_weather_icon_code = str(current_weather['weather'][0]['id'])
                return {"result": f"Das Wetter in {location} ist aktuell {current_weather['weather'][0]['description']} bei {round(current_weather['temp'])} Grad."}
            elif 0 < days_ahead <= 7:
                daily = weather_data['daily'][days_ahead]
                self.logic.last_weather_icon_code = str(daily['weather'][0]['id'])
                date_str = (datetime.date.today() + datetime.timedelta(days=days_ahead)).strftime('%A, %d.%m')
                return {"result": f"Vorhersage für {location} am {date_str}: {daily['weather'][0]['description']} bei Höchstwerten um {round(daily['temp']['day'])} Grad."}
            return {"result": "Vorhersage nur für 7 Tage möglich."}
        except Exception as e:
            logging.error(f"Wetter-Fehler: {e}")
            return {"result": "Wetterdienst nicht erreichbar."}

    # --- HIER IST DIE KORREKTUR ---
    def get_news(self, query: str, max_results: int = 3, language: str = 'de'):
        if not self.news_api_key: return {"result": "NewsAPI-Schlüssel fehlt."}
        try:
            url = f"https://newsapi.org/v2/top-headlines?q={query}&language={language}&pageSize={max_results}&apiKey={self.news_api_key}"
            data = requests.get(url, timeout=10).json()
            articles = data.get('articles', [])
            if not articles: return {"result": f"Keine Schlagzeilen zum Thema '{query}' gefunden."}
            headlines = [article['title'] for article in articles]
            return {"result": f"Top-Schlagzeilen zu '{query}': " + ". ".join(headlines)}
        except Exception as e:
            logging.error(f"News-Fehler: {e}")
            return {"result": "Nachrichtendienst nicht erreichbar."}

    def search_wikipedia(self, search_query: str):
        try:
            summary = wikipedia.summary(search_query, sentences=3, auto_suggest=True)
            return {"result": summary}
        except wikipedia.exceptions.PageError:
            return {"result": f"Ich konnte nichts zu '{search_query}' auf Wikipedia finden."}
        except Exception as e:
            return {"result": f"Wikipedia-Fehler: {e}"}

    def web_search(self, search_query: str):
        logging.info(f"Führe Websuche durch für: '{search_query}'")
        if not (self.google_cse_api_key and self.google_cse_id): return {"result": "Websuche nicht konfiguriert."}
        try:
            url = f"https://www.googleapis.com/customsearch/v1?key={self.google_cse_api_key}&cx={self.google_cse_id}&q={search_query}&num=3"
            response = requests.get(url, timeout=10).json()
            items = response.get('items', [])
            if not items: return {"result": f"Ich konnte keine Ergebnisse für '{search_query}' finden."}
            
            snippets = [f"Titel: {item.get('title')}, Info: {item.get('snippet')}" for item in items]
            return {"result": "Hier sind die Top-Ergebnisse der Websuche: " + " | ".join(snippets)}
        except Exception as e:
            logging.error(f"Web-Search Fehler: {e}")
            return {"result": "Bei der Websuche ist ein Fehler aufgetreten."}