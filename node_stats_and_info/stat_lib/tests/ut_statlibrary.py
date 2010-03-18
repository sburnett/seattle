"""
<Program Name>
  ut_statlibrary.py

<Started>
  February 12, 2010
  
<Author>
  Jeff Rasley
  jeffra45@gmail.com

<Purpose>
  Tests for the Statistics Library, to run use the Unit Test Framework (utf),
  instructions on how to run this through the UTF are below:
  https://seattle.cs.washington.edu/wiki/UnitTestFrameworkRunning
  
  User must input correct path to the Statistics Library in the area below.
"""

import sys

#--*Insert Your Path Here (stat_lib location)*--
PATH_TO_STAT_LIB = "/home/jeffra45/stat_lib/"
#----------*Insert Your Path above*--------------------

sys.path.append(PATH_TO_STAT_LIB)
import stat_library

nodes = stat_library.import_data('normal_nodes.gz')
nodes_dup = stat_library.import_data('dup_beta_key.gz')




def main():
  
  # Tests for 'normal' nodes.
  test_normal_nodes()
  test_prod_beta_key_split()
  test_versions()
  
  # Tests for 'dup' nodes
  test_dup_nodes()
  test_prod_beta_key_split_dup()




# Tests to make sure that all 'normal' nodes imported correctly.
def test_normal_nodes():
  normal_node_count = 398
  if len(nodes) != normal_node_count:
    print "Total nodes imported did not equal expected amount of " + normal_node_count




def test_prod_beta_key_split():
  
  # Expected numbers in each category for normal nodes.
  prod_count = 369
  beta_count = 28
  other_count = 1

  split_dict = stat_library.production_beta_key_split(nodes)
  split_nodes = split_dict['production_beta_key_dicts']

  if len(split_dict['nodes_with_multi_keys']) != 0:
    print "Found a node with multiple keys in what should be a normal set of nodes"

  production = split_nodes['production']
  beta = split_nodes['beta']
  other = split_nodes['other']

  # Makes sure each category has the excepted number of nodes in it.
  if len(production) != prod_count:
    print "production count did not equal expected amount of " + str(prod_count)
  if len(beta) != beta_count:
    print "beta count did not equal expected amount of " + str(beta_count)
  if len(other) != other_count:
    print "other count did not equal expected amount of " + str(other_count)




def test_versions():
  versions_correct = {'0.1p-beta-r3467':1, '0.1c':1, '0.1q-beta-r3514':26, '0.1b':1, '0.1m':1, '0.1q':368}
  versions_test = stat_library.get_versions(nodes)  

  if versions_test.keys().sort() != versions_correct.keys().sort():
    print "not all versions were accounted for"

  for version_name,count in versions_correct.items():
    if len(versions_test[version_name]) != versions_correct[version_name]:
      print "count of version " + version_name + " does not match expected value"




# Tests to make sure that all 'dupkey' nodes imported correctly.
def test_dup_nodes():
  normal_node_count = 398
  if len(nodes_dup) != normal_node_count:
    print "Total nodes imported did not equal expected amount of " + normal_node_count




def test_prod_beta_key_split_dup():

  # Expected numbers in each category for 'dupkey' nodes.
  prod_count = 368
  beta_count = 28
  other_count = 1

  split_dict = stat_library.production_beta_key_split(nodes_dup)
  split_nodes = split_dict['production_beta_key_dicts']

  if len(split_dict['nodes_with_multi_keys']) == 0:
    print "Should have found at least one node with multiple keys, but found zero."

  production = split_nodes['production']
  beta = split_nodes['beta']
  other = split_nodes['other']

  # Makes sure each category has the excepted number of nodes in it.
  if len(production) != prod_count:
    print "production count did not equal expected amount of " + str(prod_count) + ", " + str(len(production))
  if len(beta) != beta_count:
    print "beta count did not equal expected amount of " + str(beta_count)
  if len(other) != other_count:
    print "other count did not equal expected amount of " + str(other_count)




if __name__ == '__main__':
  main()
