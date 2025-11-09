# -*- coding: utf-8 -*-
# // -- Okami Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.

import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth

class SpotifyToolsPlugin:
    def __init__(self, logic_controller):
        self.logic = logic_controller

    def register(self):
        return {
            "play_spotify_song": self.play_spotify_song,
            "control_spotify_playback": self.control_spotify_playback
        }
    
    def _get_spotify_client(self):
        try:
            auth_manager = SpotifyOAuth(scope="user-read-playback-state,user-modify-playback-state")
            return spotipy.Spotify(auth_manager=auth_manager)
        except Exception as e:
            logging.error(f"Spotify-Auth-Fehler: {e}")
            return None

    def play_spotify_song(self, song_name: str, artist_name: str = None):
        sp = self._get_spotify_client()
        if not sp: return "Spotify-Client nicht verfügbar."
        query = f"track:{song_name}" + (f" artist:{artist_name}" if artist_name else "")
        results = sp.search(q=query, type='track', limit=1)
        tracks = results.get('tracks', {}).get('items', [])
        if not tracks: return f"Lied '{song_name}' nicht gefunden."
        devices = sp.devices().get('devices', [])
        if not any(d.get('is_active') for d in devices):
            self.logic.speak("Ich kann kein aktives Spotify-Gerät finden.")
            return "Kein aktives Spotify-Gerät gefunden."
        sp.start_playback(uris=[tracks[0]['uri']])
        return f"Spiele '{tracks[0]['name']}' von '{tracks[0]['artists'][0]['name']}'."

    def control_spotify_playback(self, action: str):
        sp = self._get_spotify_client()
        if not sp: return "Spotify-Client nicht verfügbar."
        action = action.lower()
        try:
            if action == 'pause': sp.pause_playback(); return "Pausiert."
            elif action == 'resume': sp.start_playback(); return "Fortgesetzt."
            elif action == 'next': sp.next_track(); return "Nächstes Lied."
            elif action == 'previous': sp.previous_track(); return "Voriges Lied."
            return f"Aktion '{action}' unbekannt."
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 404: return "Es wird gerade nichts abgespielt."
            return f"Spotify-Fehler: {e.msg}"
