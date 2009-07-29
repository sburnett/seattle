
# I'm going to neuter the calls here...
import nanny
import restrictions

def do_nothing(*args):
  pass

nanny.tattle_quantity = do_nothing
nanny.tattle_add_item = do_nothing
nanny.tattle_remove_item = do_nothing
nanny.tattle_check = do_nothing
restrictions.assertisallowed = do_nothing
from emulmisc import *
from emulcomm import *
from emulfile import *
from emultimer import *

# This is needed because otherwise we're using the old versions of file and
# open.   We should change the names of these functions when we design
# repy 0.2
originalopen = open
originalfile = file
open = emulated_open
file = emulated_open

