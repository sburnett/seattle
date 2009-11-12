import os

# If DEBUG is True, then error details will be shown on the website and ADMINS
# will not receive an email when an error occurs. So, this should be False in
# production.
DEBUG = True
TEMPLATE_DEBUG = DEBUG

# This is needed to allow xmlrpc requests to work when they don't have a slash
# on the end of the url.
APPEND_SLASH = False

# The directory the settings.py file is in is what we consider the root of the website. 
WEBSITE_ROOT = os.path.dirname(__file__)

# NOTE: File-backed sessions are broken on windows. Don't use if you're on windows!
#SESSION_ENGINE = 'django.contrib.sessions.backends.file'

# The default session file path is determined by tempfile.gettempdir(),
# which may be what we want. Modify the setting below to change this behavior. 
#SESSION_FILE_PATH = '/path/to/session/files'

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# The directory where the base installers named seattle_linux.tgz, seattle_mac.tgz,
# and seattle_win.zip are located.
BASE_INSTALLERS_DIR = "C:\dist"

# The directory in which customized installers created by seattlegeni will be
# stored. A directory within this directory will be created for each user.
USER_INSTALLERS_DIR = os.path.join(BASE_INSTALLERS_DIR, "geni")

# The url that corresponds to USER_INSTALLERS_DIR
# IMPORTANT: Always end the url with a forward slash! (/) 
USER_INSTALLERS_URL = "https://blackbox.cs.washington.edu/dist/geni/"

# The directory where we keep the public keys of the node state keys.
STATE_KEYS_DIR = os.path.join(WEBSITE_ROOT, '..', 'seattlegeni', 'node_state_transitions', 'statekeys')


ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'installer_creator'             # Or path to database file if using sqlite3.
DATABASE_USER = 'root'             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = WEBSITE_ROOT + '/html/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/site_media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin_media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '7um_ghg@0telr-50id5t(+0q0lx=+czm+5r904nd^*b4x8fmy3'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'installer_creator.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    WEBSITE_ROOT + '/html/templates'
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
)
