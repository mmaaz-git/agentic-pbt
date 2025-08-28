import os
import sys

# Add the site-packages path to sys.path
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

# Configure Django settings before importing anything from Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')

# Now try to import Django and set it up
import django
django.setup()

from simple_history.manager import (
    HistoricalQuerySet,
    HistoryManager,
    HistoryDescriptor,
    SIMPLE_HISTORY_REVERSE_ATTR_NAME
)

print("Successfully imported simple_history.manager components")
print(f"HistoricalQuerySet: {HistoricalQuerySet}")
print(f"HistoryManager: {HistoryManager}") 
print(f"HistoryDescriptor: {HistoryDescriptor}")
print(f"SIMPLE_HISTORY_REVERSE_ATTR_NAME: {SIMPLE_HISTORY_REVERSE_ATTR_NAME}")