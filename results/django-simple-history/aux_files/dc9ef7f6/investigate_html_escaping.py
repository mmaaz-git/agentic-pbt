import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

from simple_history.template_utils import HistoricalRecordContextHelper
from unittest.mock import Mock
from django.utils.safestring import mark_safe

helper = HistoricalRecordContextHelper(Mock(), Mock())
change = Mock()
change.field = 'test_field'

field_meta = Mock()
field_meta.verbose_name = 'Test Field'
helper.model._meta.get_field = Mock(return_value=field_meta)

# Test various special characters
test_cases = [
    ["'"],              # Single quote
    ['"'],              # Double quote  
    ['<'],              # Less than
    ['>'],              # Greater than
    ['&'],              # Ampersand
    ['<script>'],       # Script tag
    ['normal text'],    # Normal text
]

print("Testing HTML escaping behavior:")
print("-" * 50)
for test_list in test_cases:
    old_str, new_str = helper.stringify_delta_change_values(change, test_list, ['test'])
    print(f"Input:  {test_list}")
    print(f"Output: {old_str}")
    if str(test_list[0]) != old_str.strip('[]'):
        print(f"  → Characters were escaped!")
    print()

# Test if this is for HTML safety
print("\nAnalysis:")
print("- This appears to be intentional HTML escaping for XSS protection")
print("- The output is meant to be displayed in Django templates")
print("- Django's conditional_escape is being applied (line 155 in template_utils.py)")
print("- This ensures the output is safe for HTML display")

# Check if the escaping is actually mentioned in the code
print("\nCode inspection:")
print("Line 154-155 in stringify_delta_change_values:")
print("  # Escape *after* shortening, as any shortened, previously safe HTML strings have")
print("  # likely been mangled. Other strings that have not been shortened, should have")
print("  # their 'safeness' unchanged.")
print("  return conditional_escape(old_short), conditional_escape(new_short)")
print("\nThis is INTENTIONAL behavior for HTML safety, not a bug.")