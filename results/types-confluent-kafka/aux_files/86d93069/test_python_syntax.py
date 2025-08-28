# Test if 'world"""' is valid Python

# Test various quote patterns to understand Python's behavior

# This should be a syntax error in Python
try:
    code = 'world"""'
    compile(code, '<string>', 'exec')
    print(f"'{code}' compiled successfully (unexpected!)")
except SyntaxError as e:
    print(f"'{code}' causes SyntaxError: {e}")

# This should work - complete triple-quoted string
try:
    code = '"""hello"""'
    compile(code, '<string>', 'exec')
    print(f"'{code}' compiled successfully")
except SyntaxError as e:
    print(f"'{code}' causes SyntaxError: {e}")

# This should be an error - unclosed triple quote
try:
    code = '"""hello'
    compile(code, '<string>', 'exec')
    print(f"'{code}' compiled successfully (unexpected!)")
except SyntaxError as e:
    print(f"'{code}' causes SyntaxError: {e}")

# Test in import context
try:
    code = 'import world"""'
    compile(code, '<string>', 'exec')
    print(f"'{code}' compiled successfully (unexpected!)")
except SyntaxError as e:
    print(f"'{code}' causes SyntaxError: {e}")