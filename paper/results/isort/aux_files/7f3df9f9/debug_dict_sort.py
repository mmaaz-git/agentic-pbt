import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort.literal import _dict, ISortPrettyPrinter
from isort.settings import Config

# Test the _dict function directly
test_dict = {'a': 3, 'b': 1, 'c': 2}
printer = ISortPrettyPrinter(Config())

# Call the _dict function directly
result = _dict(test_dict, printer)
print(f"Input dict: {test_dict}")
print(f"Direct _dict output: {result}")

# Also test what sorted() does
sorted_items = sorted(test_dict.items(), key=lambda item: item[1])
print(f"Sorted items by value: {sorted_items}")
sorted_dict = dict(sorted_items)
print(f"Dict from sorted items: {sorted_dict}")

# And what pformat does to it
formatted = printer.pformat(sorted_dict)
print(f"PrettyPrinter.pformat output: {formatted}")