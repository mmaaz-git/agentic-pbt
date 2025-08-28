from packaging.requirements import Requirement

# Test the failing case
text = '0 '  # Has trailing space
req_str = f'package @ {text}'
print(f'Input URL: "{text}" (repr: {repr(text)})')
print(f'Requirement string: "{req_str}" (repr: {repr(req_str)})')

req = Requirement(req_str)
print(f'Parsed URL: "{req.url}" (repr: {repr(req.url)})')
print(f'URL matches input: {req.url == text}')
print()

# Test more cases with whitespace
print("Testing various URLs with whitespace:")
test_cases = [
    'https://example.com ',  # trailing space
    ' https://example.com',  # leading space
    ' https://example.com ',  # both
    'file:///path/to/file ',
    'https://example.com/path ',
    'test ',
    ' test',
    '\ttest',
    'test\n',
]

for url in test_cases:
    req_str = f'package @ {url}'
    try:
        req = Requirement(req_str)
        if req.url != url:
            print(f'  MISMATCH: "{url}" (repr: {repr(url)}) -> "{req.url}" (repr: {repr(req.url)})')
        else:
            print(f'  OK: "{url}"')
    except Exception as e:
        print(f'  ERROR: "{url}" -> {e}')