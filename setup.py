"""
<Author>
  richard@jordan.ham-radio-op.net

<Start Date>
  April 05, 2009

<Description>
  Distutils script.  Distutils is the classic python way to
  automate.  It supposingly takes care of portability for you.
  Also, you can register with Cheese Shop (PyPI) for easy distribution.

  Usually, it manages Python modules.  We're more into Python
  scripts, so we customize it all a bit.

  Also, we add some extra handy commands.

  References:
    http://da44en.wordpress.com/2002/11/22/using-distutils/
    http://docs.python.org/distutils/
    http://blog.ianbicking.org/pythons-makefile.html
    http://wiki.python.org/moin/Distutils/Tutorial

<Usage>
  python setup.py ...
 
  Do `python setup.py --help-commands` for available commands.
"""
from distutils.cmd import Command
from distutils.errors import *
from distutils.core import setup

import preparetest
import os
import shutil
import glob

class test(Command):
    """
    <Purpose>
      This command calls a script that erases all the files in a target folder, 
      then copies the necessary test files to the folder. Afterwards, the .mix files 
      in the target folder are run through the preprocessor. 
 
      If the folder doesn't exist, this command *will* create it for you.
    """
    description = "run the seattle preparetest.py script"
    user_options = [('include-repy-tests', 't', 'copy in the repy test files')]
    boolean_options = ['t']

    def initialize_options(self):
      """Setup defaults"""
      self.directory = "tests"
      self.include_repy_tests = False	
	
    def finalize_options(self):
      """ What do we have?"""
      pass

    def run(self):
      """Do a little setup, then pass off to old python script"""

      # remove dir if exists
      if (os.path.exists(self.directory)):  
        if os.path.isdir(self.directory):
          shutil.rmtree(self.directory)
        else:    
          os.remove(self.directory)

      # recreate it
      os.mkdir(self.directory)    

      # pass off to preparetest.py
      cmd = "python preparetest.py " + str(self.directory)
      if self.include_repy_tests:
        cmd += " -t"
      os.system(cmd)

class demokit(Command):
    """
    <Purpose>
      This command generates a folder of Repy and some
      other files.  This generated demokit folder is a distribution of Repy.
 
      Creates a directory called "demokit".  If "demokit" exists,
      overwrites it.
    """
    description = "build the demokit"
   
    user_options = []

    def initialize_options(self):
      """Setup defaults"""
      self.directory = "demokit"

    def finalize_options(self):
      """See what we have"""
      pass

    def run(self):
      """Do it"""
      #store root directory and get target directory
      target_dir = self.directory
      current_dir = os.getcwd()

      # remove demokit if exists
      if (os.path.exists(target_dir)):  
        if os.path.isdir(target_dir):
          shutil.rmtree(target_dir)
        else:
          os.remove(target_dir)    

      # recreate it
      os.mkdir(target_dir)

      # Build Repy
      preparetest.copy_to_target("nodemanager/servicelogger.mix", target_dir)
      preparetest.copy_to_target("repy/*.py", target_dir)
      preparetest.copy_to_target("seattlelib/*.repy", target_dir)
      preparetest.copy_to_target("portability/*.py", target_dir)
      preparetest.copy_to_target("nodemanager/advertise.mix", target_dir)
      preparetest.copy_to_target("nodemanager/persist.py", target_dir)
      preparetest.copy_to_target("nodemanager/timeout_xmlrpclib.py", target_dir)
      preparetest.copy_to_target("nodemanager/openDHTadvertise.py", target_dir)

      # add some utils
      preparetest.copy_to_target("seattlelib/repypp.py", target_dir)
      preparetest.copy_to_target("seash/seash.mix", target_dir)

      # and some extras
      preparetest.copy_to_target("repy/apps/allpairsping/allpairsping.repy", target_dir)
      preparetest.copy_to_target("repy/apps/old_demokit/*", target_dir)

      # and even some other
      preparetest.copy_to_target("LICENSE.TXT", target_dir)

      #set working directory to the test folder
      os.chdir(target_dir)

      #call the process_mix function to process all mix files in the target directory
      preparetest.process_mix("repypp.py")

      # rm mix src files
      files_to_remove = glob.glob("*.mix")
      for fn in files_to_remove: 
        os.remove(fn)

      #go back to root project directory
      os.chdir(current_dir) 
  # run()

class clean(Command):
    """
    <Purpose>
      This command removes the junk of other commands.  It also deletes .pyc
      files.
    """

    user_options = [ ]

    def initialize_options(self):
      """Setup"""

      # these are the junk dirs from other commands
      self._junk = ['demokit', 'tests']

    def finalize_options(self):
      """What now"""
      pass

    def run(self):
      """Delete it all"""

      # Remove .pyc files
      pycs = [ ]
      for dirpath, dirnames, filenames in os.walk('.'):
        for fname in filenames:
          if fname.endswith('.pyc'):
            os.remove(os.path.join(dirpath, fname))
         
      # Remove junk directories
      for junker in self._junk:
        if (os.path.exists(junker)):
          if os.path.isdir(junker):
            shutil.rmtree(junker)
          else:
            os.remove(junker)







"""
<Purpose>
  Main interface to Distutils.

<Usage>
  cmdclass
    Add new commands to the cmdclass dictionary.

  scripts
    Add other scripts here and modify build_scripts
    to correctly build them.
 
<Else>
  All other details are metadata.  Distutils uses
  then to register your project with Cheese Shop
  as well as generate user help messages.
"""
setup(name = "Seattle",
      version = "0.1e",
      author = 'Justin Cappos', 
      author_email="seattle-devel@cs.washington.edu",	
      maintainer = 'Ivan Beschastnikh',
      maintainer_email="seattle-devel@cs.washington.edu",	
      url = "http://seattle.cs.washington.edu",
      description = "a platform for networking and distributed systems research",
      long_description = """
Seattle is a platform for networking and distributed systems research. It's free, community-driven, and offers a large deployment of computers spread across the world. 
Seattle works by operating on resources donated by users and institutions. It's currently targeted for use by educators teaching networking and distributed systems 
classes. The global distribution of the Seattle network provides the ability to use it in application contexts that include cloud computing, peer-to-peer networking, 
ubiquitous/mobile computing, distributed systems. 
""",
      keywords = "seattle repy",
      license = "GENI Public License",

      scripts = ['repy.py', 'seash.py'],
      cmdclass = { "test": test, "demokit": demokit, "clean": clean })

