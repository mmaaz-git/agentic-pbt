import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')
import jurigged.runpy

# Test _run_code with tuple code
code_before = compile("x = 1", "<test>", "exec")
code_after = compile("y = 2", "<test>", "exec")

run_globals = {}
result = jurigged.runpy._run_code(
    code=(code_before, code_after),
    run_globals=run_globals
)

assert 'x' in result
assert 'y' in result
assert result['x'] == 1
assert result['y'] == 2
print("Test 1 passed: tuple code execution")

# Test with prepare callback
prepare_called = []

def prepare(globals_dict):
    prepare_called.append(True)
    globals_dict['injected'] = 'from_prepare'

run_globals = {}
code = compile("x = 1", "<test>", "exec")
result = jurigged.runpy._run_code(
    code=code,
    run_globals=run_globals,
    prepare=prepare
)

assert prepare_called == [True]
assert 'injected' in result
print("Test 2 passed: prepare callback")

# Test tuple with prepare - checking call order
code_before = compile("x = 1", "<test>", "exec")
code_after = compile("y = x + 1", "<test>", "exec")

prepare_calls = []

def prepare2(globals_dict):
    prepare_calls.append(globals_dict.get('x'))
    globals_dict['z'] = 3

run_globals = {}
result = jurigged.runpy._run_code(
    code=(code_before, code_after),
    run_globals=run_globals,
    prepare=prepare2
)

assert prepare_calls == [1]
assert result['x'] == 1
assert result['y'] == 2
assert result['z'] == 3
print("Test 3 passed: tuple with prepare callback order")

print("\nAll execution tests passed!")