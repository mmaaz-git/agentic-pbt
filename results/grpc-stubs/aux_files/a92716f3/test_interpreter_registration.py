import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import re

# Import the module we're testing
from cloudscraper.interpreters import JavaScriptInterpreter, interpreters


# Test 1: Check that multiple interpreters are registered
def test_interpreters_registered():
    """Check that interpreters are properly registered"""
    # After imports, there should be some interpreters registered
    assert len(interpreters) > 0, "No interpreters were registered"
    
    # Check known interpreters
    expected_interpreters = ['js2py', 'nodejs']  # Based on our file reading
    for name in expected_interpreters:
        assert name in interpreters, f"Expected interpreter '{name}' not found in registry"


# Test 2: Dynamic import functionality
def test_dynamic_import():
    """Test the dynamicImport class method"""
    # Try to import a known interpreter
    try:
        js2py_interp = JavaScriptInterpreter.dynamicImport('js2py')
        assert js2py_interp is not None
        assert 'js2py' in interpreters
        assert interpreters['js2py'] is js2py_interp
    except ImportError:
        # This might happen if the interpreter wasn't properly initialized
        pass


# Test 3: Verify interpreter is instance of JavaScriptInterpreter
def test_interpreter_type_check():
    """All registered interpreters should be instances of JavaScriptInterpreter"""
    for name, interpreter in interpreters.items():
        # The check in dynamicImport uses isinstance
        assert isinstance(interpreter, JavaScriptInterpreter), f"Interpreter '{name}' is not a JavaScriptInterpreter instance"


# Test 4: solveChallenge number formatting
class TestInterpreter(JavaScriptInterpreter):
    def __init__(self):
        super().__init__('test_interpreter')
    
    def eval(self, jsEnv, js):
        # Return different numeric values for testing
        return self.test_value

# Test various numeric values for formatting
@given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False))
def test_solve_challenge_formatting(value):
    """solveChallenge should format numbers to 10 decimal places"""
    interp = TestInterpreter()
    interp.test_value = value
    
    try:
        result = interp.solveChallenge("dummy_body", "dummy_domain")
        # Check that it's formatted as a string with 10 decimal places
        assert isinstance(result, str)
        # Should match the pattern of a number with exactly 10 decimal places
        assert re.match(r'-?\d+\.\d{10}$', result), f"Result '{result}' doesn't have exactly 10 decimal places"
        
        # Verify the value is correct
        float_result = float(result)
        assert abs(float_result - value) < 1e-9, f"Formatting changed the value significantly"
    except Exception as e:
        # solveChallenge catches all exceptions and raises CloudflareSolveError
        assert 'CloudflareSolveError' in str(type(e))


# Test 5: solveChallenge error handling
def test_solve_challenge_error_handling():
    """solveChallenge should raise CloudflareSolveError on eval failure"""
    class FailingInterpreter(JavaScriptInterpreter):
        def __init__(self):
            super().__init__('failing_interpreter')
        
        def eval(self, jsEnv, js):
            raise ValueError("Intentional eval failure")
    
    interp = FailingInterpreter()
    
    from cloudscraper.exceptions import CloudflareSolveError
    
    try:
        result = interp.solveChallenge("body", "domain")
        assert False, "Should have raised CloudflareSolveError"
    except CloudflareSolveError as e:
        assert 'Error trying to solve Cloudflare IUAM Javascript' in str(e)
    except Exception as e:
        assert False, f"Wrong exception type: {type(e)}"


# Test 6: Edge case - eval returns non-numeric value
def test_solve_challenge_non_numeric():
    """solveChallenge should handle non-numeric eval results"""
    class StringInterpreter(JavaScriptInterpreter):
        def __init__(self):
            super().__init__('string_interpreter')
        
        def eval(self, jsEnv, js):
            return "not a number"
    
    interp = StringInterpreter()
    
    from cloudscraper.exceptions import CloudflareSolveError
    
    try:
        result = interp.solveChallenge("body", "domain")
        assert False, "Should have raised CloudflareSolveError for non-numeric result"
    except CloudflareSolveError:
        pass  # Expected
    except Exception as e:
        assert False, f"Wrong exception type: {type(e)}"


# Test 7: Test interpreter registry isolation
@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=20))
def test_interpreter_registry_unique_names(name):
    """Each interpreter name should map to exactly one interpreter instance"""
    if name in interpreters:
        # Get the existing interpreter
        existing = interpreters[name]
        
        # Try to create another with the same name
        class DuplicateInterpreter(JavaScriptInterpreter):
            def __init__(self):
                super().__init__(name)
            
            def eval(self, jsEnv, js):
                return 42
        
        # Create the duplicate
        dup = DuplicateInterpreter()
        
        # The registry should now have the new one, replacing the old
        assert interpreters[name] is dup
        assert interpreters[name] is not existing