"""
<Program Name>
  get_seattlestopper_lock.py

<Started>
  June 4, 2009

<Author>
  Zachary Boka

<Purpose>
  Removes the 'seattlestopper' lock being held by any program
  (e.g., seattlestopper.py).  This program is meant to be included in the
  start_seattle script, just before the nmmain.py and softwareupdater.py
  programs.
"""

import runonce
import nonportable

# Zack: Removed the code that explicitly called nmmain.py and softwareupdater.py
def main():
  lockstate = runonce.getprocesslock("seattlestopper")
  while lockstate != True and lockstate:
    nonportable.portablekill(lockstate)
    lockstate = runonce.getprocesslock("seattlestopper")


if __name__ == "__main__":
  main()
