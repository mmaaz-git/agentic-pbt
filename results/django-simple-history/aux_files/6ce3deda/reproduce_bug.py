import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

from simple_history.template_utils import ObjDiffDisplay

try:
    display = ObjDiffDisplay(max_length=30)
    print("Created ObjDiffDisplay with max_length=30")
except AssertionError as e:
    print(f"AssertionError with max_length=30")

try:
    display = ObjDiffDisplay(max_length=38)
    print("Created ObjDiffDisplay with max_length=38")
except AssertionError as e:
    print(f"AssertionError with max_length=38")

try:
    display = ObjDiffDisplay(max_length=39)
    print("Created ObjDiffDisplay with max_length=39")
except AssertionError as e:
    print(f"AssertionError with max_length=39")

print("\nDemonstrating the issue:")
print("With default parameters: min_begin_len=5, placeholder_len=12, min_common_len=5, min_end_len=5")
print("Minimum required max_length = 5 + 12 + 5 + 12 + 5 = 39")
print("Any max_length < 39 will trigger an AssertionError")