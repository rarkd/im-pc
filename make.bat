@ECHO OFF
REM BFCPEOPTIONSTART
REM Advanced BAT to EXE Converter www.BatToExeConverter.com
REM BFCPEEXE=
REM BFCPEICON=
REM BFCPEICONINDEX=-1
REM BFCPEEMBEDDISPLAY=0
REM BFCPEEMBEDDELETE=1
REM BFCPEADMINEXE=0
REM BFCPEINVISEXE=0
REM BFCPEVERINCLUDE=0
REM BFCPEVERVERSION=1.0.0.0
REM BFCPEVERPRODUCT=Product Name
REM BFCPEVERDESC=Product Description
REM BFCPEVERCOMPANY=Your Company
REM BFCPEVERCOPYRIGHT=Copyright Info
REM BFCPEWINDOWCENTER=1
REM BFCPEDISABLEQE=0
REM BFCPEWINDOWHEIGHT=30
REM BFCPEWINDOWWIDTH=120
REM BFCPEWTITLE=Window Title
REM BFCPEOPTIONEND
@ECHO OFF
TITLE BY RARA_NAFUKU
COLOR 0B

:MENU
CLS
ECHO ================================
ECHO            CIT UKK
ECHO ================================
ECHO.
ECHO  [1] V1 192.168.80.   0-255
ECHO  [2] V2 192.168.1.    0-255
ECHO  [3] V3 192.168.10.   0-255
ECHO  [4] Keluar
ECHO.
ECHO ================================
ECHO.
SET /P pilih="Pilih menu: "

IF "%pilih%"=="1" GOTO KONTOL
IF "%pilih%"=="2" GOTO MENU
IF "%pilih%"=="3" GOTO MENU
IF "%pilih%"=="4" GOTO KELUAR
ECHO Pilihan tidak valid!
TIMEOUT /T 2 >NUL
GOTO MENU

:PILIHAN2
CLS
ECHO ================================
ECHO        PILIHAN 2
ECHO ================================
ECHO.
ECHO Ini adalah menu pilihan 2
ECHO.
PAUSE
GOTO MENU

:PILIHAN3
CLS
ECHO ================================
ECHO        PILIHAN 3
ECHO ================================
ECHO.
ECHO Ini adalah menu pilihan 3
ECHO.
PAUSE
GOTO MENU

:KONTOL
@echo off
echo By Rara_Nafuku

REM Create output directory if it doesn't exist
if not exist "C:\Users\USER\GNS3\configs" mkdir "C:\Users\USER\GNS3\configs"

REM Change to the output directory
cd /d "C:\Users\USER\GNS3\configs"

REM Download using PowerShell
powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/rarkd/ukk/archive/refs/heads/master.zip' -OutFile 'ukk.zip'}"

REM Extract the zip file
powershell -Command "& {Expand-Archive -Path 'ukk.zip' -DestinationPath '.' -Force}"

REM Clean up zip file
del ukk.zip
move "C:\Users\USER\GNS3\configs\fufufafaV1.exe" "C:\Users\USER\Desktop"

echo Download complete!
echo By Rara_Nafuku
echo Pergunakan Dengan Bijak!!
pause
GOTO MENU

:KELUAR
CLS
ECHO LOLOT!!
TIMEOUT /T 2 >NUL
EXIT