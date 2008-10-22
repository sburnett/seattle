"""
Brent Couvrette
October 19, 2008

Note:  When running these tests on Windows, be sure to comment out
the lines invoking ps, as these will obviously fail.  You will have
to manually look at the task manager instead :(.

Also, currently only either the rsync tests or the restart test can
be run.  If both are set to run, the restart test will fail.  This
should probably be fixed at some point, but for now, be sure to 
comment out the statements in one of the sections.

Usage:
Run this after having run test_updater and copied the folders made
there to the update site you supply as an argument here.
See test_updater.py for more details.

python test_runupdate.py <baseurl>

"""
import subprocess
import sys
import time

def runRsyncTest(testtype, updateurl, otherargs=[]):
	# Run the test
	rsync = subprocess.Popen(['python', 'test_rsync.py', testtype]+otherargs+[updateurl], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

	# Get the output
	theout = rsync.stdout.read()
	rsync.stdout.close()

	# Return the output
	return theout

def main():
	if len(sys.argv) < 2:
		print 'Must supply base url!'
		
	baseurl = sys.argv[1]
	############################
	# Run the rsync only tests #
	############################
	
	# Run the noup test (Nothing should fail, nothing should be updated)
#	print runRsyncTest('-x', baseurl+'noup/')
	
	# Run the wronghash test(There should be an RsyncError, and no updates)
#	print runRsyncTest('-e', baseurl+'wronghash/')
	
	# Run the badkeysig test (There should be no updates)
#	print runRsyncTest('-x', baseurl+'badkeysig/')
	
	# Run the corruptmeta test (there should be an RsyncError, and no updates)
#	print runRsyncTest('-e', baseurl+'corruptmeta/')

	# Run the updatenmmain test (only nmmain should get updated)
#	print runRsyncTest('-u', baseurl+'updatenmmain/', ['nmmain.py', 'metainfo'])
	
	#####################################
	# Finished running rsync only tests #
	#####################################
	
	##################################
	# Software updater restart tests #
	##################################
	updateprocess = subprocess.Popen(['python', 'softwareupdater.py'])
	ps = subprocess.Popen('ps -ef | grep "python softwareupdater.py" | grep -v grep', shell=True, stdout=subprocess.PIPE)
	psout = ps.stdout.read()
	print 'Initial ps out:'
	print psout
	if psout == '':
		print 'Failure to start initially'
		
	# Wait for 2 minutes for the update to happen and the
	# process to die.
	for junk in range(60):
		if updateprocess.poll() != None:
			break
		time.sleep(2)
	
	ret = updateprocess.returncode
	print 'Return code is: '+str(ret)
	if ret != 10:
		print 'Wrong return code! '+str(ret)
	else:
		ps = subprocess.Popen('ps -ef | grep "python softwareupdater.py" | grep -v grep', shell=True, stdout=subprocess.PIPE)
		psout = ps.stdout.read()
		psout.strip()
		print 'After ps out:'
		print psout
		if psout == '':
			print 'New updater failed to start!'
		else:
			print 'softwareupdater restart success!'
		
	
	######################################
	# End Software updater restart tests #
	######################################
	
if __name__ == '__main__':
	main()
