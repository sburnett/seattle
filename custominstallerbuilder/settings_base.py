"""
<Program Name>
  settings_base.py

<Started>
  September 2010

<Author>
  Alex Hanson

<Purpose>
  A standard Django settings file with sensible defaults for the Custom
  Installer Builder. Defaults may be overridden with a host-specific settings
  file.
"""

import os


#####################
## DJANGO SETTINGS ##
#####################

LANGUAGE_CODE = 'en-us'

ROOT_URLCONF = 'custominstallerbuilder.urls'

TEMPLATE_CONTEXT_PROCESSORS = (
  'django.core.context_processors.debug',
  'django.core.context_processors.media',
  'django.core.context_processors.request',
)

TEMPLATE_LOADERS = (
  'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
  'django.middleware.common.CommonMiddleware',
  'django.contrib.sessions.middleware.SessionMiddleware',
  
  'custominstallerbuilder.common.logging.AutoLogger',
)

INSTALLED_APPS = (
  'django.contrib.sessions',
  
  'custominstallerbuilder.common',
  'custominstallerbuilder.html',
  'custominstallerbuilder.xmlrpc',
)


######################
## SEATTLE SETTINGS ##
######################

API_VERSION = '2.0'

RSA_BIT_LENGTH = 1024

RESERVED_PERCENTAGE = 20
RESERVED_PUBLIC_KEY = ('22599311712094481841033180665237806588790054310631' +
                       '22212640538127192408957390862714329251678153065241' +
                       '18066213798225790714155936570886371161495933379772' +
                       '45852950266439908269276789889378874571884748852746' +
                       '04564336805810746002111791865754241307679148613009' +
                       '19631126128545917895186908567467573124723623322592' +
                       '77422867 '                                          +
                       '12178066700672820207562107598028055819349361776558' +
                       '37461088735487045522615055669952637546486391375031' +
                       '34279683626214107639968565432115029780129789820957' +
                       '21782038963923296750730921093699612004441897097001' +
                       '47453137576874628755013536139396199508236250310488' +
                       '33646534106312288966536664564631008506093439882030' +
                       '07196015297634940347643303507210312220744678194150' +
                       '28696628270130764506497467631616708900317832551835' +
                       '98633442778145515591974745904830447335743299259475' +
                       '70794508677779986459413166439000241765225023677767' +
                       '75455528219624191550099684271351183095435347543920' +
                       '91092498566442787450810470298799990224622309574271' +
                       '58692886317487753201883260626152112524674984510719' +
                       '26971542234003862082668443174813132566994006440475' +
                       '71206017273628813172226993934080975969813558102579' +
                       '55915922792648825991943804005848347665699744316223' +
                       '96385126385185348333569932187148396617648083929312' +
                       '54130576035617245982276177369442602699941116102868' +
                       '27287926594015501020767105358832476708899657514473' +
                       '42315337751466064169938344506536919972404338007214' +
                       '62465370395773906592436407103393295066205750341750' +
                       '16766639538091937167987100329247642670588246573895' +
                       '99025121172183951771379041317064617724621636602985' +
                       '36040314219321231671154448349084245569926629359811' +
                       '66395451031277981021820123445253')


#############################
## HOST-SPECIFIC SETTINGS ##
############################

# These settings can be overridden in your local/settings.py file. The values
# below are just sensible defaults or examples.

# Unless you are actively debugging, these should be set to False.
DEBUG = False
TEMPLATE_DEBUG = DEBUG

SECRET_KEY = '***** This should be changed to a random string *****'

ADMINS = (('Seattle developers', 'seattle-devel@cs.washington.edu'),)
MANAGERS = ADMINS

TIME_ZONE = 'America/Los_Angeles'

SESSION_ENGINE = 'django.contrib.sessions.backends.file'

# Where to find things on the filesystem.
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'html', 'static')
BASE_INSTALLER_ROOT = os.path.join(MEDIA_ROOT, 'installers', 'base')
CUSTOM_INSTALLER_ROOT = os.path.join(MEDIA_ROOT, 'installers')

# Where to find things through the web server.
BASE_URL = 'http://example.com/'
PROJECT_URL = BASE_URL + 'custominstallerbuilder/'
MEDIA_URL = PROJECT_URL + 'static/'
BASE_INSTALLER_URL = PROJECT_URL + 'static/installers/base/'
CUSTOM_INSTALLER_URL = PROJECT_URL + 'static/installers/'

# During testing, you may want to use Django's built-in static file server.
SERVE_STATIC = False
STATIC_BASE = 'static/'

# Android keystore settings
ANDR_KEYSTORE_PATH = ''
ANDR_KEYSTORE_PASS = ''
ANDR_KEY_PASS = ''
ANDR_KEY_NAME = ''
