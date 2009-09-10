@echo off
REM Change into the seattle_repy directory.
FOR /F "tokens=*" %%A IN ('cd') DO SET OrigDir=%%A
SET TargetPath=%~f0
SET TargetDir=%TargetPath:stop_seattle.bat=%
cd %TargetDir%

start /min pythonw impose_seattlestopper_lock.py
echo.seattle has been stopped.

REM Go back up to the seattle directory.
cd ..