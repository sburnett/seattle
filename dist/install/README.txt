Procedure for changing Windows installer (will eventually be automated):
1. Extract all files from win.zip into win\.
2. Make necessary changes to install.bat or to RUNME.bat (the script that will eventually start seattle from the install directory).
3. Run an svn update on the trunk.
4. Go to the trunk and run "python preparetest.py dist\install\win\files".
5. Go to dist\install\win\files and run "python nminit.py".
6. In most cases, it won't be necessary to change the python\ directory, but if you think you need to (i.e. if we are updating the version of python we use), make sure to check the python_info.txt file first.
7. Zip the win\ folder back up into win.zip, and distribute!