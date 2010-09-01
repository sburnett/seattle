#!/usr/bin/python

"""
<Program Name>
  ut_analyzer_correct_behaviour.py

<Started>
  August 25, 2010

<Author>
  Jeff Rasley
  jeffra45@gmail.com

<Purpose>
  This program is used with the Unit Test Framework to check to see if
  analyzer.py is categorizing/analyzing correctly for multiple 'correct'
  nodes with multiple log files.
"""



import sys
import pickle
import gzip


# **Insert path to Analyzer below.**
sys.path.append('/home/jeffra45/log_analyzer/')
import analyzer





PATH_TO_LOGS = '/home/jeffra45/log_analyzer/tests/unit_test_logs/'




def ut_correct_dir_of_nodes_all_time():
  
  dir_of_nodes_path = PATH_TO_LOGS + 'correct_node_dirs/'
  node_dict = analyzer.analyze_dirs(dir_of_nodes_path)

  answer = _open_answer(PATH_TO_LOGS + 'correct_multi_logs_answer.pik')
#  answer = _save_answer(PATH_TO_LOGS + 'correct_multi_logs_answer.pik', node_dict)

  if node_dict != answer:
    print "The test for multiple nodes with multiple log files has failed!"




def ut_correct_dir_of_nodes_custom_time():
  single_log_path = PATH_TO_LOGS + 'correct_node_dirs/'
  timestamp = 1283097094.98
  node_dict = analyzer.analyze_dirs(single_log_path, False, timestamp)

  # Open and load the answer for this unit test.
  answer_path = PATH_TO_LOGS + 'correct_multi_logs_answer_custom_time.pik'
  answer = _open_answer(answer_path)
#  answer = _save_answer(answer_path, node_dict)

  if node_dict != answer:
    print "The test for a multiple nodes with multuple log files using a",
    print "custom timestamp", timestamp, "has failed!"




def _open_answer(name_of_pickle):
  answer_fd = gzip.open(name_of_pickle + '.gz','r')
  answer = pickle.load(answer_fd)
  answer_fd.close()
  return answer




def _save_answer(name_of_pickle, object):
  answer_fd = gzip.open(name_of_pickle + '.gz', 'w')
  pickle.dump(object, answer_fd)
  answer_fd.close()




def main():
  ut_correct_dir_of_nodes_all_time()
  ut_correct_dir_of_nodes_custom_time()




if __name__ == '__main__':
  main()
