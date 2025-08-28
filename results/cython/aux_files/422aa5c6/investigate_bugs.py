import Cython.Tempita

# Bug 1: Non-ASCII identifier issue
print('=== Bug 1: Non-ASCII identifiers ===')
try:
    template = Cython.Tempita.Template('{{µ}}')
    result = template.substitute(µ='value')
    print(f'Result: {result}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')

# Check if Python itself accepts µ as identifier
µ = 'test'
print(f'Python accepts µ as identifier: {µ}')

# Bug 2: Reserved keywords in templates
print('\n=== Bug 2: Reserved keywords ===')
try:
    template = Cython.Tempita.Template('{{else}}')
    result = template.substitute(**{'else': 'value'})
except Exception as e:
    print(f'Error with else: {type(e).__name__}: {e}')

# Bug 3: None doesn't raise NameError
print('\n=== Bug 3: None handling ===')
try:
    template = Cython.Tempita.Template('{{None}}')
    result = template.substitute()
    print(f'Result with None: {repr(result)}')
except NameError as e:
    print(f'NameError as expected: {e}')

# Bug 4: Empty string in for loop
print('\n=== Bug 4: Empty strings in for loop ===')
template = Cython.Tempita.Template('''{{for item in items}}{{item}}
{{endfor}}''')
result = template.substitute(items=[''])
print(f'Result with empty string: {repr(result)}')
print(f'Lines: {result.split(chr(10))}')

# Bug 5: Empty expression
print('\n=== Bug 5: Empty expression ===')
try:
    template = Cython.Tempita.Template('{{}}')
    result = template.substitute()
    print(f'Result: {repr(result)}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')