@echo off 
IF EXIST "C:\Users\Carter\AppData\Local\Temp\uninstall.bat" GOTO already_copied 
GOTO copy 
:copy 
copy uninstall.bat "C:\Users\Carter\AppData\Local\Temp\uninstall.bat" > nul 2> nul 
start /min "C:\Users\Carter\AppData\Local\Temp\uninstall.bat" 
GOTO end 
:already_copied 
echo del /f /q "C:\Users\Carter\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\seattle.bat" > nul 2> nul 
rmdir /s /q "C:\Users\Carter\Documents\seattle_repy" > nul 2> nul 
GOTO end 
:end 
