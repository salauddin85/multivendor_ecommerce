from .base import *

# Silk development setting
SILKY_PYTHON_PROFILER = True
SILKY_PYTHON_PROFILER_BINARY = True
SILKY_PYTHON_PROFILER_RESULT_PATH = os.path.join(MEDIA_ROOT, 'silk-profiles')
os.makedirs(SILKY_PYTHON_PROFILER_RESULT_PATH, exist_ok=True)
# To disable profiling for static files, etc.
SILKY_IGNORE_PATHS = ['/static/*', '/admin/*']

# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

print("Running server using development settings")
