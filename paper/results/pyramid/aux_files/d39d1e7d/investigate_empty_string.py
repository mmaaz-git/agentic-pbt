import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.encode import urlencode
from urllib.parse import parse_qs

# Test case from hypothesis
query = {'0': ''}
result = urlencode(query)
print(f"urlencode({query}) = '{result}'")

# Parse it back  
parsed = parse_qs(result)
print(f"parse_qs('{result}') = {parsed}")

# Also check with keep_blank_values
parsed_with_blanks = parse_qs(result, keep_blank_values=True)
print(f"parse_qs('{result}', keep_blank_values=True) = {parsed_with_blanks}")

# Check what standard library does
from urllib.parse import urlencode as std_urlencode
std_result = std_urlencode(query)
print(f"std urlencode({query}) = '{std_result}'")