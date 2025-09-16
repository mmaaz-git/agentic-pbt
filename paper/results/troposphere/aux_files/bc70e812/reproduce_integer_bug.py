import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer

test_values = [1.5, 2.7, -3.14, 100.1]

for value in test_values:
    try:
        result = integer(value)
        print(f"integer({value}) = {result}, type: {type(result)}")
        print(f"  int({result}) = {int(result)}")
    except (ValueError, TypeError) as e:
        print(f"integer({value}) raised: {e}")

print("\nAccording to the function documentation, it should validate integers.")
print("But it accepts floats without raising an error!")