from .base import *

# Silk Production settings
SILKY_PYTHON_PROFILER = False
SILKY_PYTHON_PROFILER_BINARY = False
SILKY_META = False


# max file size settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024      # 50MB per file
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024      # 50MB total per request


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv("DB_NAME"),
        'USER': os.getenv("DB_USER"),
        'PASSWORD': os.getenv("DB_PASSWORD"),
        'HOST': os.getenv("DB_HOST"),
        'PORT': os.getenv("DB_PORT"),
    }
}

print("Running server using production settings")
