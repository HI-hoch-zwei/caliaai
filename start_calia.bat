@echo off
ECHO =======================================================
ECHO  C.A.L.I.A. Startsequenz wird eingeleitet...
ECHO =======================================================

SET "BASE_PATH=%~dp0"
SET "MONGO_DIR=%BASE_PATH%Calia_AI\mongodb"
SET "DB_PATH=%BASE_PATH%Calia_AI\data\db"
SET "APP_DIR=%BASE_PATH%Calia_AI\app"
SET "MONGO_PORT=27017"

ECHO [1/3] Pruefe MongoDB-Verzeichnis...
IF NOT EXIST "%MONGO_DIR%\bin\mongod.exe" (
    ECHO FEHLER: MongoDB konnte in "%MONGO_DIR%" nicht gefunden werden.
    pause
    exit /b
)

ECHO [2/3] Starte MongoDB im Hintergrund...
IF NOT EXIST "%DB_PATH%" (
    ECHO Erstelle Datenbankverzeichnis: %DB_PATH%
    mkdir "%DB_PATH%"
)

start "MongoDB" /min "%MONGO_DIR%\bin\mongod.exe" --dbpath "%DB_PATH%" --port %MONGO_PORT%

ECHO Warte auf MongoDB-Initialisierung (Port %MONGO_PORT%)...

REM --- KORRIGIERTE WARTESCHLEIFE (für deutsches Windows) ---
:wait_for_mongo
ECHO Pruefe Port %MONGO_PORT%...

REM Wir suchen nur nach dem Port.
netstat -an | find ":%MONGO_PORT%" >nul

REM IF NOT ERRORLEVEL 1 bedeutet "Befehl war erfolgreich" (Port gefunden)
IF NOT ERRORLEVEL 1 (
    ECHO Port gefunden. Pruefe, ob er bereit ist...
    REM Kurze extra Sekunde, um sicherzustellen, dass der Port "abhört"
    timeout /t 1 /nobreak >nul
    GOTO :mongo_ready
)

REM Port ist noch nicht bereit, warte 1 Sekunde
timeout /t 1 /nobreak >nul
GOTO :wait_for_mongo

:mongo_ready
ECHO MongoDB ist bereit und laeuft.

ECHO [3/3] Starte C.A.L.I.A. Hauptanwendung...
cd /d "%APP_DIR%"
call venv\Scripts\activate.bat && python Calia.py

ECHO =======================================================
ECHO  C.A.L.I.A. wurde beendet.
ECHO =======================================================
pause