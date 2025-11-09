# -*- coding: utf-8 -*-
# // -- Okami Digital Fingerprint -- //
# This code is the intellectual property of its creator and is protected under patent (Patent-No. 30 2025 240 538.7).
# Unauthorized use, reproduction, or distribution is strictly prohibited.
# Project: C.A.L.I.A AI.

import datetime
from asteval import Interpreter as SafeEvaluator

# Jedes Plugin ist eine Klasse. Das macht es sauber und organisiert.
class BasicToolsPlugin:
    def __init__(self, logic_controller):
        # Wir übergeben den 'logic_controller' (die Haupt-CaliaLogic-Instanz),
        # damit das Plugin bei Bedarf auf Config etc. zugreifen kann.
        self.logic = logic_controller
        self.config = self.logic.config

    def register(self):
        # Diese Methode gibt ein Wörterbuch mit den Werkzeugen zurück,
        # die dieses Plugin zur Verfügung stellt.
        return {
            "calculate": self.calculate,
            "get_current_time": self.get_current_time
        }

    # --- Die eigentliche Logik der Werkzeuge ---
    # Beachte, dass dies exakt die gleichen Methoden sind, die vorher in CaliaLogic waren.

    def calculate(self, expression: str):
        self.logic.gui.set_state('thinking') # Beispiel für Zugriff auf die GUI
        safe_expression = expression.replace('^', '**').replace('x', '*').replace(',', '.')
        try:
            aeval = SafeEvaluator()
            result = aeval.eval(safe_expression)
            return f"Das Ergebnis von {expression} ist {result}."
        except Exception:
            return "Ich konnte diesen Ausdruck nicht berechnen."

    def get_current_time(self):
        return f"Es ist {datetime.datetime.now().strftime('%H:%M')} Uhr."
