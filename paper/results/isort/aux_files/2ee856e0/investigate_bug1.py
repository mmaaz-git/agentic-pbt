"""Investigate the module placement bug with special characters."""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort.settings import Config
from isort.place import module, module_with_reason
import isort.sections as sections

# Test case that failed: module name '$'
test_module = '$'

# Configure it as first-party
config = Config(known_first_party=frozenset([test_module]))

# Get the placement
placement, reason = module_with_reason(test_module, config)

print(f"Module: {test_module}")
print(f"Expected placement: {sections.FIRSTPARTY}")
print(f"Actual placement: {placement}")
print(f"Reason: {reason}")
print(f"Config known_first_party: {config.known_first_party}")

# Test with other special characters
special_modules = ['$', '@', '#', '!', '%', '&', '*', '(', ')']
for mod in special_modules:
    config = Config(known_first_party=frozenset([mod]))
    placement = module(mod, config)
    print(f"Module '{mod}': placed in {placement} (expected {sections.FIRSTPARTY})")
    
# Test if the issue is in the matching logic
print("\n--- Testing matching logic ---")
config = Config(known_first_party=frozenset(['$']))
print(f"'$' in config.known_first_party: {'$' in config.known_first_party}")

# Let's trace through the logic
print("\n--- Detailed trace for '$' ---")
name = '$'
config = Config(known_first_party=frozenset([name]))

# Check if it's being caught by _known_pattern
from isort.place import _known_pattern
result = _known_pattern(name, config)
print(f"_known_pattern result: {result}")

# Look at the known_patterns
print(f"config.known_patterns: {list(config.known_patterns)[:5]}...")  # First 5 patterns