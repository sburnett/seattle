@echo off
cd "%PROG_PATH%"
start /min /wait pythonw.exe get_seattlestopper_lock.py
start /min pythonw.exe nmmain.py
start /min pythonw.exe softwareupdater.py
echo.seattle has been started.