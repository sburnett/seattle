@echo off

:check_os
REM Check for Vista or XP
IF "%ALLUSERSPROFILE%"=="C:\ProgramData" GOTO set_vista
GOTO set_xp

:set_vista
set PROG_PATH=%HOMEDRIVE%%HOMEPATH%\Documents\seattle_repy
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
GOTO :check_seattle_installed

:set_xp
set PROG_PATH=%HOMEDRIVE%%HOMEPATH%\My Documents\seattle_repy
set STARTUP_FOLDER=%HOMEDRIVE%%HOMEPATH%\Start Menu\Programs\Startup
GOTO :check_seattle_installed

:check_seattle_installed
IF EXIST "%PROG_PATH%" GOTO seattle_installed
GOTO seattle_not_installed

:seattle_installed
ECHO seattle is already installed on your computer.
GOTO failure

:seattle_not_installed
GOTO copy_files

:check_for_python
REM Repeat as necessary for all supported versions of Python
IF EXIST "C:\Python26" GOTO python_26_installed
IF EXIST "C:\Python25" GOTO python_25_installed
IF EXIST "C:\Python24" GOTO python_24_installed

GOTO python_not_installed

:python_26_installed
set PYTHON_LIB=C:\Python26\Lib
GOTO check_for_extensions

:python_25_installed
set PYTHON_LIB=C:\Python25\Lib
GOTO check_for_extensions

:python_24_installed
set PYTHON_LIB=C:\Python24\Lib
GOTO check_for_extensions

:python_not_installed
echo Python not installed or out of date.
echo Please follow the instructions to install Python on your computer.
python-2.6.msi
IF EXIST "C:\Python26" GOTO python_26_installed
echo Failed to install Python. Please try again, or download and install Python separately.
GOTO failure

:check_for_extensions
IF EXIST "%PYTHON_LIB%\site-packages\win32" GOTO extensions_installed
echo Required package pywin32 not installed.
echo Please follow the instructions to install pywin32 on your computer.
GOTO extensions_not_installed

:extensions_installed
GOTO copy_files

:copy_files
mkdir "%PROG_PATH%"
xcopy "files\*" "%PROG_PATH%\" /E /Y > nul 2> nul
xcopy "python\*" "%PROG_PATH%\" /E /Y > nul 2> nul
GOTO add_to_startup

:add_to_startup
echo @echo off > seattle.bat
echo "%PROG_PATH%\python.exe" "%PROG_PATH%\nmmain.py" >> seattle.bat
echo exit >> seattle.bat
copy seattle.bat "%STARTUP_FOLDER%\" > nul
GOTO generate_uninstaller

:generate_uninstaller
echo @echo off > uninstall.bat
echo IF EXIST "%TMP%\uninstall.bat" GOTO already_copied >> uninstall.bat
echo GOTO copy >> uninstall.bat
echo :copy >> uninstall.bat
echo copy uninstall.bat "%TMP%\uninstall.bat" ^> nul 2^> nul >> uninstall.bat
echo start /min "%TMP%\uninstall.bat" >> uninstall.bat
echo GOTO end >> uninstall.bat
echo :already_copied >> uninstall.bat
echo echo del /f /q "%STARTUP_FOLDER%\seattle.bat" ^> nul 2^> nul >> uninstall.bat
echo rmdir /s /q "%PROG_PATH%" ^> nul 2^> nul >> uninstall.bat
echo GOTO end >> uninstall.bat
echo :end >> uninstall.bat
copy uninstall.bat "%PROG_PATH%\" > nul 2> nul
GOTO success

:extensions_not_installed
IF "%PYTHON_LIB%"=="C:\Python26\Lib" pywin32-212.win32-py2.6.exe
IF "%PYTHON_LIB%"=="C:\Python25\Lib" pywin32-212.win32-py2.5.exe
IF "%PYTHON_LIB%"=="C:\Python24\Lib" pywin32-212.win32-py2.4.exe
IF EXIST "%PYTHON_LIB%\site-packages\win32" GOTO extensions_installed
echo Failed to install the pywin32 extensions for Python.
echo Please try again or install them on your own before trying again.
GOTO failure

:failure
echo Installation failed.
GOTO end

:success
echo seattle was successfully installed on your computer.
"%STARTUP_FOLDER%\seattle.bat"
GOTO end

:end