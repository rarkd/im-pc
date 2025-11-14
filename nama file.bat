:PILIHAN1
CLS
ECHO ================================
ECHO      BUAT PROGRAM BARU
ECHO ================================
ECHO.

REM Buat direktori jika belum ada
IF NOT EXIST "C:\Users\USER\Documents\hc" (
    MKDIR "C:\Users\USER\Documents\hc"
    ECHO Direktori berhasil dibuat
    ECHO.
)

REM Minta nama file
SET /P namafile="Masukkan nama file (tanpa .bat): "

REM Buat file batch baru
(
echo @echo off
echo echo Downloading files from GitHub...
echo.
echo REM Create output directory if it doesn't exist
echo if not exist "C:\Users\USER\Documents\hc" mkdir "C:\Users\USER\Documents\hc"
echo.
echo REM Change to the output directory
echo cd /d "C:\Users\USER\Documents\hc"
echo.
echo REM Download using PowerShell
echo powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/rarkd/lala/archive/refs/heads/master.zip' -OutFile 'lala.zip'}"
echo.
echo REM Extract the zip file
echo powershell -Command "& {Expand-Archive -Path 'lala.zip' -DestinationPath '.' -Force}"
echo.
echo REM Clean up zip file
echo del lala.zip
echo.
echo echo Download complete!
echo echo Files saved to: C:\Users\USER\Documents\hc
echo pause
) > "C:\Users\USER\Documents\hc\%namafile%.bat"

ECHO.
ECHO File berhasil dibuat di:
ECHO C:\Users\USER\Documents\hc\%namafile%.bat
ECHO.
PAUSE
GOTO MENU