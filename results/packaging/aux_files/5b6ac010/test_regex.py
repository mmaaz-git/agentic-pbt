import re

# The actual regex pattern from packaging.utils
pattern = r'^([a-z0-9]|[a-z0-9]([a-z0-9-](?!--))*[a-z0-9])$'
regex = re.compile(pattern)

# Test various cases
test_cases = [
    '0',      # single char
    '00',     # two chars
    '0-0',    # with single dash
    '0--0',   # with double dash
    '000',    # three chars
    '0-0-0',  # with dashes
    'a--b',   # letters with double dash
    'foo--bar',  # longer with double dash
    'a-b',    # simple valid case
]

for test in test_cases:
    match = regex.match(test)
    print(f'{test!r}: {bool(match)}')