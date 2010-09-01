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
  analyzer.py is categorizing/analyzing correctly for a 'correct' log file.
"""



import sys
import pickle
import gzip


# **Insert path to Analyzer below.**
sys.path.append('/home/jeffra45/log_analyzer/')
import analyzer





PATH_TO_LOGS = '/home/jeffra45/log_analyzer/tests/unit_test_logs/'




def ut_correct_single_log_all_time():

  single_log_path = PATH_TO_LOGS + 'correct_single_log'
  log_dict = analyzer.analyze_log(single_log_path)

  # Open and load the answer for this unit test.
  answer = _open_answer(PATH_TO_LOGS + 'correct_single_log_answer.pik')
   
  if log_dict != answer:
    print "The test for a single log, checking all timestamps failed!"




def ut_correct_single_log_custom_time():

  single_log_path = PATH_TO_LOGS + 'correct_single_log'
  timestamp = 1283097094.98
  log_dict = analyzer.analyze_log(single_log_path, False, timestamp)

  # Open and load the answer for this unit test.
  answer_path = PATH_TO_LOGS + 'correct_single_log_answer_custom_time.pik'
  answer = _open_answer(answer_path)

  if log_dict != answer:
    print "The test for a single log, checking timestamps after:", timestamp,
    print "failed!"




def ut_correct_single_log_saved_time():

  single_log_path = PATH_TO_LOGS + 'correct_single_log'

  # Read in timestamp so we can save it for later use.
  timestamp_file = open(single_log_path + '.timestamp','r')
  timestamp_contents = timestamp_file.read()
  timestamp_file.close()

  log_dict = analyzer.analyze_log(single_log_path, True)

  # Since we are using the saved time option we must restore the original 
  # timestamp since it was overwritten during runtime.
  timestamp_file = open(single_log_path + '.timestamp','w')
  timestamp_file.write(timestamp_contents)
  timestamp_file.close()
  
  # Open and load the answer for this unit test.
  answer_path = PATH_TO_LOGS + 'correct_single_log_answer_saved_time.pik'
  answer = _open_answer(answer_path)

  if log_dict != answer:
    print "The test for a single log, using the most recently stored",
    print "timestamp has failed!",




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
  ut_correct_single_log_all_time()
  ut_correct_single_log_custom_time()
  ut_correct_single_log_saved_time()




if __name__ == '__main__':
  main()
