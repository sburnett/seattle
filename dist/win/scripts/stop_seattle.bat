@echo off
cd "%PROG_PATH%"
start /min pythonw impose_seattlestopper_lock.py
echo.seattle has been stopped.