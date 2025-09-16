import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

from sphinxcontrib.mermaid.autoclassdiag import get_classes
from sphinxcontrib.mermaid.exceptions import MermaidError

print("Testing get_classes with edge case inputs...")

# Test 1: Empty module name "."
print("\nTest 1: get_classes('.')")
try:
    list(get_classes('.'))
    print("Success - no error raised")
except MermaidError as e:
    print(f"MermaidError raised (expected): {e}")
except ValueError as e:
    print(f"ValueError raised (BUG - should be MermaidError): {e}")
except Exception as e:
    print(f"Unexpected error: {type(e).__name__}: {e}")

# Test 2: Path separator "/"
print("\nTest 2: get_classes('/')")
try:
    list(get_classes('/'))
    print("Success - no error raised")
except MermaidError as e:
    print(f"MermaidError raised (expected): {e}")
except ValueError as e:
    print(f"ValueError raised (BUG - should be MermaidError): {e}")
except Exception as e:
    print(f"Unexpected error: {type(e).__name__}: {e}")

# Test 3: Normal invalid module name for comparison
print("\nTest 3: get_classes('definitely_not_a_module')")
try:
    list(get_classes('definitely_not_a_module'))
    print("Success - no error raised")
except MermaidError as e:
    print(f"MermaidError raised (expected): {e}")
except Exception as e:
    print(f"Unexpected error: {type(e).__name__}: {e}")