"""
Executes a few help commands and make sures seash prints out the correct output.
Make sure to update the txt file of the expected output if help's contents have
modified
"""
# Seash's module system outputs a list of enabled modules on load.
# We need to instruct the UTF to ignore that.
#pragma out Enabled modules:
#pragma out To see a list of all available modules, use the 'show modules' command.
import seash
import sys


orig_stdout = sys.stdout
sys.stdout = open("test_results.txt", "w")
command_list = [
  'help show',
  'enable geoip',
  'help show',
  'help show location',
  ]

seash.command_loop(command_list)



sys.stdout.close()

# Compares the test results with the expected text that should have been printed
# out when executing the series of help commands
sys.stdout = orig_stdout

test_results = open("test_results.txt", "r")
wanted_results = open("help_dynamic_test_results.txt", "r")

open('asdf.txt', 'w').write(test_results.read())
test_results = open("test_results.txt", "r")

original = wanted_results.readlines()
actual = test_results.readlines()

for i in range(len(original)):
  if not original[i] == actual[i]:
    print "Line " + str(i) + " of test results are not consistent with expected results: help_test_results.txt"



test_results.close()
wanted_results.close()

# Disable the modules we used
seash.command_loop(['disable geoip'])