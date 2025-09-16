import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

from unittest.mock import Mock
from simple_history.middleware import _context_manager
from simple_history.models import HistoricalRecords

# Create two mock requests
request1 = Mock()
request1.id = "outer"

request2 = Mock()
request2.id = "inner"

# Test nested context managers
print("Testing nested context managers...")
print(f"Initial state - has request: {hasattr(HistoricalRecords.context, 'request')}")

with _context_manager(request1):
    print(f"Outer context - request id: {HistoricalRecords.context.request.id}")
    
    with _context_manager(request2):
        print(f"Inner context - request id: {HistoricalRecords.context.request.id}")
    
    # After inner context exits, outer context should be restored
    try:
        print(f"Back to outer context - request id: {HistoricalRecords.context.request.id}")
    except AttributeError as e:
        print(f"BUG: Lost outer context! Error: {e}")

print(f"After all contexts - has request: {hasattr(HistoricalRecords.context, 'request')}")