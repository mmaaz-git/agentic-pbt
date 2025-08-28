import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

from simple_history.template_utils import ObjDiffDisplay

# Test case 1: AssertionError with small max_length
print("Testing ObjDiffDisplay with small max_length values...")
try:
    display = ObjDiffDisplay(max_length=10)
    print(f"max_length=10: Success")
except AssertionError as e:
    print(f"max_length=10: AssertionError - min_diff_len calculation results in negative value")

try:
    display = ObjDiffDisplay(max_length=30)
    print(f"max_length=30: Success")
except AssertionError as e:
    print(f"max_length=30: AssertionError - min_diff_len calculation results in negative value")

# Let's calculate what the minimum safe max_length is
# min_diff_len = max_length - (min_begin_len + placeholder_len + min_common_len + placeholder_len + min_end_len)
# min_diff_len = max_length - (5 + 12 + 5 + 12 + 5)
# min_diff_len = max_length - 39
# For min_diff_len >= 0, we need max_length >= 39

print("\nCalculating minimum safe max_length...")
min_required = 5 + 12 + 5 + 12 + 5  # Default values
print(f"Minimum required max_length: {min_required}")

try:
    display = ObjDiffDisplay(max_length=38)
    print(f"max_length=38: Success")
except AssertionError:
    print(f"max_length=38: AssertionError")

try:
    display = ObjDiffDisplay(max_length=39)
    print(f"max_length=39: Success")
except AssertionError:
    print(f"max_length=39: AssertionError")

# Test case 2: HTML escaping in stringify_delta_change_values
print("\n\nTesting HTML escaping issue...")
from simple_history.template_utils import HistoricalRecordContextHelper
from unittest.mock import Mock

helper = HistoricalRecordContextHelper(Mock(), Mock())
change = Mock()
change.field = 'test_field'

field_meta = Mock()
field_meta.verbose_name = 'Test Field'
helper.model._meta.get_field = Mock(return_value=field_meta)

# Test with a single quote
test_list = ["'"]
old_str, new_str = helper.stringify_delta_change_values(change, test_list, ['new_item'])

print(f"Input list: {test_list}")
print(f"Output string: {old_str}")
print(f"Expected: ['] but got: {old_str}")
print(f"Single quote was HTML-escaped to &#x27;")