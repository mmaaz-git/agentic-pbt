import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

# Test the interpreter loading mechanism
from cloudscraper.interpreters import interpreters, JavaScriptInterpreter

print("Initial interpreters:", interpreters)

# Try dynamic import
try:
    js2py_interp = JavaScriptInterpreter.dynamicImport('js2py')
    print("After dynamic import of js2py:", interpreters)
except ImportError as e:
    print(f"Failed to import js2py: {e}")

# Try another one
try:
    nodejs_interp = JavaScriptInterpreter.dynamicImport('nodejs')
    print("After dynamic import of nodejs:", interpreters)
except ImportError as e:
    print(f"Failed to import nodejs: {e}")

# Now test if the registered interpreters work
for name, interp in interpreters.items():
    print(f"Interpreter {name}: {type(interp)}")
    
# Test edge case: import non-existent interpreter
try:
    fake_interp = JavaScriptInterpreter.dynamicImport('nonexistent')
    print("ERROR: Should have failed to import nonexistent interpreter")
except ImportError as e:
    print(f"Correctly failed to import nonexistent: {e}")

# Test another edge case: What happens if we try to import the same interpreter twice?
if 'js2py' in interpreters:
    first_instance = interpreters['js2py']
    try:
        js2py_again = JavaScriptInterpreter.dynamicImport('js2py')
        second_instance = interpreters['js2py']
        if first_instance is second_instance:
            print("Same instance returned on second import (correct)")
        else:
            print("ERROR: Different instance returned on second import")
    except Exception as e:
        print(f"Error on second import: {e}")