""" 
Author: Brent Couvrette

Start Date: October 16, 2008

Description:
Currently creates all necesary test folders locally.  Currently
it is upto the runner of these tests to then copy these files 
to whatever update site location they wish, then run the actual
test runner.

How to successfully run all the tests:
Get all necesary files into a single folder contained within an empty folder 
(this makes things simpler), make sure the software updater has the right url
and is configured with updater.publickey
Run:
python test_updater.py
cd ..
scp -r * <update site specified in softwareupdater.py minus a updater/ >
cd back into the directory with all the files
python test_runupdate.py <same place you scp'ed to>
Then the tests will hopefully run!
If not, email Brent Couvrette with questions at couvb@cs.washington.edu
"""

import ftplib
import glob
import os
import writemetainfo
import tempfile
import shutil
import sys

def write_meta_and_copy(destdir, keyname):

  # create the metainfo file for the files in the current directory
  writemetainfo.create_metainfo_file(keyname+'.privatekey', keyname+'.publickey')

  print 'Copying files to '+destdir+' folder...'

  # Copy these files into the destdir directory.
  os.mkdir('../'+destdir)
  for seaFile in glob.glob('*'):
    if not os.path.isdir(seaFile):
      shutil.copy(seaFile, '../'+destdir+'/')
			
			
def main():
  # Update folders need a metainfo file and all of the files needed
  # for the Seattle platform.  The metainfo file must contain all of 
  # the file names, their hashes, and their sizes.  The metainfo file
  # must be correctly signed.  Of course for sites testing error 
  # conditions, these things might not hold.

  # Make sure a metainfo file already exists.
  file('metainfo', 'w').close()

  # Change softwareupdater wait time to be only 30 seconds
  # instead of 5-55 minutes.
  upfile = file('softwareupdater.py', 'r')
  updata = upfile.read()
  upfile.close()
  sleepindex = updata.find('do_sleep(1800+random.randint(-1500,1500))')
  eolindex = updata.find('\n', sleepindex)
  updata = updata[:sleepindex]+'do_sleep(30)'+updata[eolindex:]

  # Write this change back to softwareupdater
  upfile = file('softwareupdater.py', 'w')
  upfile.write(updata)
  upfile.close()

  print 'Writing initial metainfo...'	
  # This is the directory which should have no updates, but be otherwise
  # correct.
  write_meta_and_copy('noup', 'updater')
	
  print 'Copying files to wronghash directory'
  # Copy these files into the wronghash directory.
  os.mkdir('../wronghash')
  for seaFile in glob.glob('*'):
    if not os.path.isdir(seaFile):
      shutil.copy(seaFile, '../wronghash/')


  print 'Changing nmmain...'
	
  # Make changes to nmmain.py (change version to be 0.2a)
  # Read in the current nmmain.py
  nmmainfile = file('nmmain.py', 'r')
  nmmaindata = nmmainfile.read()
  nmmainfile.close()

  # replace 'version = "xxxx"' with version = "0.2a"
  vindex = nmmaindata.find('version = "')
  nmmaindata = nmmaindata[:vindex] + 'version = "0.2a"' + nmmaindata[vindex+16:]

  # write this change back to nmmain.py
  nmmainfile = file('nmmain.py', 'w')
  nmmainfile.write(nmmaindata)
  nmmainfile.close()
	
  print 'Writing updated nmmain.py metainfo...'
  # This is the directory which should be fully correct, and just update nmmain.py
  write_meta_and_copy('updatenmmain', 'updater')
	
  # copy the new metainfo to the wrong hash directory
  # thusly causing it to have the wrong has for nmmain.py
  shutil.copy('../updatenmmain/metainfo', '../wronghash/metainfo')

  # Replace the metainfo with a faulty one!
  corruptmeta = """softwareupdater.py e0fe4093dbefcfd5b6cc7ebbee84693f07dcaf56 47253
softwareupdater.logfile 4eff5359eac7ad3635de6f8db6b672f43d2ba98f 435
generatekeys.py 4bf284e36ce95656086bd324308d00eb6c4eb92c 16036
writemetainfo.py e6c00469d77bd645a43b9ae7b734af66ed231d6a 40524

!90828751313604138861138199375516065418794160799843599128558705100285394924191002288444206024669046851496823164408997538063597164575888556545759466459359562498107740756089920043807948902332473328246320686052784108549174961107584377257390484702552802720358211058670482304929480676775120529587723588725818443641 525084957612029403526131505174200975825703127251864132403159502859804160822964990468591281636411242654674747961575351961726000088901250174303367500864513464050509705219791304838934936387279630515658887485539659961265009321421059720176716708947162824378626801571847650024091762061008172625571327893613638956683252812460872115308998220696100462293803622250781016906532481844303936075489212041575353921582380137171487898138857279657975557703960397669255944572586836026330351201015911407019810196881844728252349871706989352500746246739934128633728161609865084795375265234146710503588616865119751368455059611417010662656542444610089402595766154466648593383612532447541139354746065164116466397617384545008417387953347319292748418523709382954073684016573202764322260104572053850324379711650017898301648724851941758431577684732732530974197468849025690865821258026893591314887586229321070660394639970413202824699842662167602380213079609311959732523089738843316936618119004887003333791949492468210799866238487789522341147699931943938995266536008571314911956415053855180789361316551568462200352674864453587775619457628440845266789022527127587740754838521372486723001413117245220232426753242675828177576859824828400218235780387636278112824686701!3427231820.08!3429823820.08!None! 125740452642801122413589619983669421696565605573782518988353681684886764378935241667686552782607145445846178128152833882670479596459084186669452892413647453009337341325661198223439329207719672873005660561229581609845994574478443861613716429764919373271790891748812419690087768147344612804044476749332886840255771775932582168837202066359014516496105501760005489196992508645926245789405726683741363642923896865902733685224086970278567104375289171539590868952797257518647949953051675373553205285216077298282469530912081965173578973728773654667319880854720575354374839511535841745264135513608310479796586823472438590393013066965640128827997028418998890839035902732904327622180831039263804581451049739157493972668935655698075669501732497154480932327496433935020779023098405963146171520573204392073870050631199879639571475713546956683210092998929257182878198251749183888844749490663541795928039988676798208367636396235163214890780004476046647719487892600345368610757409664885482835076129336060699287905331433653276534440321864613491650380198474900119710044512059623896071092405925597528534821755075668563946205555303786150878687460343620312057236645398863406150824476788385388191303121369846631657314414806473449015825464142777881846154939"""

  corruptmetafile = file('metainfo', 'w')
  corruptmetafile.write(corruptmeta)
  corruptmetafile.close()
	
  print 'Copying files to corruptmeta folder...'

  # Copy these files into the corruptmeta directory.
  os.mkdir('../corruptmeta')
  for seaFile in glob.glob('*'):
    if not os.path.isdir(seaFile):
      shutil.copy(seaFile, '../corruptmeta/')
	
  print 'Writing badly signed metainfo'
  # This directory should be fully correct, except the metainfo file is 
  # signed by the wrong key!  If the key were to be accepted, there would
  # be an update to nmmain.py.
  write_meta_and_copy('badkeysig', 'badkey')
	
  print 'Changing softwareupdater'
  # Make changes to softwareupdater.py (add a comment at the end)
  upfile = file('softwareupdater.py', 'r')
  updata = upfile.read()
  upfile.close()
  updata = updata + '# Updated comment!'

  # Write this change back to softwareupdater
  upfile = file('softwareupdater.py', 'w')
  upfile.write(updata)
  upfile.close()
  
  print 'Writing updated softwareupdater.py metainfo'
  # This is the directory that will update the software updater,
  # thus causing the software updater to restart.
  write_meta_and_copy('updater', 'updater')

  # copy the original softwareupdater back
  shutil.copy('../noup/softwareupdater.py', 'softwareupdater.py')	
		

  # The current directory must be put back into it's original state,
  # so that the noup test will indeed include no changes.
  print 'Copying back files from noup folder...'
  shutil.copy('../noup/nmmain.py', 'nmmain.py')
  shutil.copy('../noup/metainfo', 'metainfo')

  print 'Upload the noup, updatenmmain, badkeysig, corruptmeta, updater, and wronghash directories to your upload site now, then run test_runupdate.py'
	
		
if __name__ == '__main__':
  main()

