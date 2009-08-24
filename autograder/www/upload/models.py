"""
<Program Name>
  models.py

<Started>
  January 16, 2008

<Author>
  ivan@cs.washington.edu
  Ivan Beschastnikh

<Purpose>
  Defines django model classes which are interfaces between django
  applications and the database

  This file contains definitions of model classes which are used by
  django to (1) create the django (autograder) database schema, (2) to
  define an interface between django applications and the database and
  are used to maintain an evolvable schema that is easy to read,
  modify, and operate on.

  See http://docs.djangoproject.com/en/dev/topics/db/models/

<ToDo>
  Right now the autograder does not make use of the database
"""

from django.db import models

# Create your models here.
