@echo off
start /min /wait pythonw.exe get_seattlestopper_lock.py
start /min pythonw.exe nmmain.py
start /min pythonw.exe softwareupdater.py
