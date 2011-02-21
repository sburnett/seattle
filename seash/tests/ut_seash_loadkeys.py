"""
Loads a series of keys and make sures seash recognizes them correctly.
"""
import seash
import sys


orig_stdout = sys.stdout
sys.stdout = open("test_results.txt", "w")
command_list = [
  'loadpub guest0',
  'loadpriv guest1', 
  'loadkeys guest2', 
  'show keys', 
  'show identities'
  ]

seash.command_loop(command_list)

sys.stdout.close()


# Compare the results to make sure key values and identities as recognized
# by seash are identical.
sys.stdout = orig_stdout

test_results = open("test_results.txt", "r")
wanted_results = open("loadkeys_test_results.txt", "r")

original = wanted_results.readlines()
actual = test_results.readlines()

for i in range(len(original)):
  if not original[i].startswith(actual[i]):
    print "Line " + str(i) + " of test results are not consistent with expected results: loadkeys_test_results.txt"

test_results.close()
wanted_results.close()

