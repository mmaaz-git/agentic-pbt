import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean

# Test the bug: boolean(0.0) should raise ValueError but returns False
test_values = [0.0, 1.0, -1.0, 0.5, -0.0]

for value in test_values:
    try:
        result = boolean(value)
        print(f"boolean({value}) = {result} (expected ValueError)")
    except ValueError:
        print(f"boolean({value}) raised ValueError (expected)")