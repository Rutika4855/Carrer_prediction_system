import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "career_prediction_system.settings")

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()
