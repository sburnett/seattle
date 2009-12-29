@echo off
REM Change into the seattle_repy directory
FOR /F "tokens=*" %%A IN ('cd') DO SET OrigDir=%%A
SET TargetPath=%~f0
SET TargetDir=%TargetPath:start_seattle.bat=%
cd %TargetDir%

start /min pythonw.exe nmmain.py
start /min pythonw.exe softwareupdater.py

REM Go back up to the seattle directory.
cd ..