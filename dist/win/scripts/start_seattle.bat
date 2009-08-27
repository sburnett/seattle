@echo off
if not exist "%PROG_PATH%" goto REMOVAL
cd "%PROG_PATH%"
start /min /wait pythonw.exe get_seattlestopper_lock.py
start /min pythonw.exe nmmain.py
start /min pythonw.exe softwareupdater.py
echo.seattle has been started.
goto END
:REMOVAL
del "%STARTER_FILE%"
:END