@echo off
TITLE C.A.L.I.A - MongoDB Server (USB)

:: %~d0 ist der Laufwerksbuchstabe des USB-Sticks (z.B. X:)
:: Wir bauen die Pfade von hier aus auf.
SET MONGO_BASE_PATH=%~d0\Calia_AI\mongodb
SET MONGO_BIN_PATH=%MONGO_BASE_PATH%\bin
SET DB_PATH=%MONGO_BASE_PATH%\data\db

ECHO ===================================================
ECHO  Starte MongoDB Server vom USB-Stick...
ECHO.
ECHO    MongoDB Executable: %MONGO_BIN_PATH%\mongod.exe
ECHO    Datenbank-Pfad: %DB_PATH%
ECHO ===================================================

:: Erstelle den Datenbankordner, falls er nicht existiert
if not exist "%DB_PATH%" (
    ECHO Erstelle Datenbank-Verzeichnis...
    mkdir "%DB_PATH%"
)

:: Starte den MongoDB Daemon (Server) ueber den kompletten Pfad
"%MONGO_BIN_PATH%\mongod.exe" --dbpath "%DB_PATH%"

:: Halte das Fenster offen, um Server-Logs zu sehen
pause