import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

from unittest.mock import Mock
from simple_history.middleware import HistoryRequestMiddleware
from simple_history.models import HistoricalRecords

# Simulate a scenario with nested middleware calls
# This could happen in Django when middleware is nested or reentrant

def simulate_nested_middleware():
    outer_request = Mock()
    outer_request.user = Mock()
    outer_request.user.username = "alice"
    
    inner_request = Mock()
    inner_request.user = Mock()
    inner_request.user.username = "bob"
    
    def inner_view(req):
        print(f"Inner view - user: {HistoricalRecords.context.request.user.username}")
        return "inner_response"
    
    def outer_view(req):
        print(f"Outer view start - user: {HistoricalRecords.context.request.user.username}")
        
        # Simulate calling another middleware-wrapped view
        inner_middleware = HistoryRequestMiddleware(inner_view)
        inner_response = inner_middleware(inner_request)
        
        # After inner middleware completes, we should still have outer context
        try:
            print(f"Outer view end - user: {HistoricalRecords.context.request.user.username}")
            return f"outer_response (contains {inner_response})"
        except AttributeError as e:
            print(f"ERROR: Lost outer request context! {e}")
            return "outer_response (context lost)"
    
    outer_middleware = HistoryRequestMiddleware(outer_view)
    result = outer_middleware(outer_request)
    print(f"Final result: {result}")

print("Simulating nested middleware scenario...")
simulate_nested_middleware()