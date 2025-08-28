import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.encode import quote_plus

# Test quote_plus with non-ASCII safe character
char = "€"
result = quote_plus(char, safe="€")
print(f"quote_plus('€', safe='€') = '{result}'")
print(f"  Expected: '€' (unencoded)")
print(f"  Got: '{result}' - {'✓ PASS' if '€' in result else '✗ FAIL'}")

# Another test
char = "ñ"
result = quote_plus(char, safe="ñ")
print(f"\nquote_plus('ñ', safe='ñ') = '{result}'")
print(f"  Expected: 'ñ' (unencoded)")
print(f"  Got: '{result}' - {'✓ PASS' if 'ñ' in result else '✗ FAIL'}")