#!/usr/bin/env python
"""
This script is a quick fix for the fact that the current version of seattle
geni is not properly updating the user records in the database to give
the user credit for their donations. That is, currently even if a donation
is processed correctly, the user's vcount_via_donations field is never
updated to be ten times the number of donations they have made.

See: https://seattle.cs.washington.edu/ticket/548

The idea is to cron this script to run frequently until we finish the
rewrite of seattlegeni.
"""

import os
import sys
sys.path.insert(0, '/home/geni/geni_production')
os.environ['DJANGO_SETTINGS_MODULE'] = 'geni_private.settings'

from geni.control.models import Donation
from geni.control.models import User


for currentuser in User.objects.all():
  
  # Get all of the active donations.
  num_donations = Donation.objects.filter(user=currentuser).filter(active=1).count()
  
  # Determine how many credits for donations the user should have.
  vessel_credits_via_donations = num_donations * 10
  
  # If the number of donation credits the user should have is wrong, update it.
  if vessel_credits_via_donations != currentuser.vcount_via_donations:

    print("User " + str(currentuser) + " has " + str(currentuser.vcount_via_donations) +
          " donation credits but should have " + str(vessel_credits_via_donations))

    currentuser.vcount_via_donations = vessel_credits_via_donations
    currentuser.save()
    print " => updated"


