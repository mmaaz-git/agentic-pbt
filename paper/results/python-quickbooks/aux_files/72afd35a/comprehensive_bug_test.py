import json
import decimal
import sys

# Add the quickbooks package path
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from quickbooks.mixins import ToJsonMixin, DecimalEncoder

# Demonstrate the bug's impact on JSON serialization
class TestObject(ToJsonMixin):
    def __init__(self):
        self.price = decimal.Decimal('19.99')
        self.quantity = decimal.Decimal('5')
        self.tax_rate = decimal.Decimal('0.08')
        self.total = decimal.Decimal('107.95')

print("Testing json_filter behavior with Decimal values:")
print("=" * 50)

obj = TestObject()
filter_func = obj.json_filter()
filtered = filter_func(obj)

print("Filtered dict contents:")
for key, value in filtered.items():
    print(f"  {key}: {value} (type: {type(value).__name__})")

print("\nAttempting to serialize filtered dict directly with json.dumps:")
try:
    json_str = json.dumps(filtered)
    print(f"Success: {json_str}")
except TypeError as e:
    print(f"Error: {e}")

print("\nUsing to_json method (which uses DecimalEncoder):")
json_str = obj.to_json()
print(f"Success - JSON output:\n{json_str}")

print("\nThe bug: json_filter claims to handle Decimals but doesn't convert them")
print("to strings in the dict values, only at the top level of the lambda.")
print("This inconsistency could cause issues when the filtered dict is used")
print("without the DecimalEncoder.")