
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

