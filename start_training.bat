@echo off
TITLE C.A.L.I.A - Vollautomatisches KI-Training

:: Definiere den Pfad zum Anwendungsordner, wo die Python-Skripte liegen.
SET APP_PATH=%~d0\Calia_AI\app

ECHO =================================================================
ECHO   C.A.L.I.A - Vollautomatisches Training des NLU-Modells
ECHO =================================================================
ECHO.
ECHO Anwendungspfad wird auf %APP_PATH% gesetzt.
ECHO.

:: Wechselt in das Verzeichnis, in dem die Python-Dateien und die venv liegen
cd /d "%APP_PATH%"
IF %ERRORLEVEL% NEQ 0 (
    ECHO FEHLER: Das Anwendungsverzeichnis '%APP_PATH%' wurde nicht gefunden!
    pause
    exit /b
)

:: 1. Virtuelle Umgebung aktivieren
ECHO --- 1. Aktiviere virtuelle Python-Umgebung ---
IF NOT EXIST "venv\Scripts\activate.bat" (
    ECHO FEHLER: Virtuelle Umgebung 'venv' im Verzeichnis %CD% nicht gefunden!
    ECHO Bitte sicherstellen, dass die venv im 'app'-Ordner liegt.
    pause
    exit /b
)
call venv\Scripts\activate.bat
ECHO Python-Umgebung ist aktiv.
ECHO.

:: 2. MongoDB Server in einem neuen Fenster starten
ECHO --- 2. Starte MongoDB Server in einem neuen Fenster ---
:: Die start_mongo.bat liegt im Hauptverzeichnis des Laufwerks (%~d0)
start "MongoDB Server" cmd /c "call %~d0\start_mongo.bat"

:: Kurze Pause, damit der Server hochfahren kann
ECHO Warte 10 Sekunden, bis die Datenbank bereit ist...
timeout /t 10
ECHO.

:: 3. Datenbank mit Intents befuellen
ECHO --- 3. Setze die Intent-Datenbank auf (loeschen und neu befuellen) ---
python setup_intents_db.py
ECHO Datenbank wurde erfolgreich befuellt.
ECHO.

:: 4. Das KI-Modell trainieren
ECHO --- 4. Starte das Training des KI-Modells ---
ECHO Die Trainings-Logs werden zusaetzlich in einer .txt-Datei gespeichert.
python train_model.py
ECHO.
ECHO ===================================================
ECHO   Das Training wurde erfolgreich abgeschlossen!
ECHO ===================================================
ECHO.

:: 5. MongoDB Server wieder beenden
ECHO --- 5. Beende den MongoDB Server ---
taskkill /F /IM mongod.exe >nul 2>&1
ECHO MongoDB Server wurde beendet.
ECHO.

:: Deaktivieren der venv (optional, da das Skript endet)
call venv\Scripts\deactivate.bat

pause