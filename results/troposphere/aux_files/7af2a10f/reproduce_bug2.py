"""Reproduce integer validator accepting floats bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import codedeploy
from troposphere.validators import integer

print("Testing integer validator with float 0.0:")
try:
    result = integer(0.0)
    print(f"integer(0.0) returned: {result!r} (type: {type(result)})")
    print(f"int(result) = {int(result)}")
    print("This is concerning - floats are being accepted as integers!")
except (ValueError, TypeError) as e:
    print(f"Correctly rejected: {e}")

print("\nTesting integer validator with float 3.14:")
try:
    result = integer(3.14)
    print(f"integer(3.14) returned: {result!r} (type: {type(result)})")
    print(f"int(result) = {int(result)}")
except (ValueError, TypeError) as e:
    print(f"Correctly rejected: {e}")

print("\nTesting TimeBasedCanary with float values:")
try:
    tbc = codedeploy.TimeBasedCanary(
        CanaryInterval=0.0,
        CanaryPercentage=50.0
    )
    print(f"TimeBasedCanary created with float values!")
    dict_result = tbc.to_dict()
    print(f"to_dict() result: {dict_result}")
except (TypeError, ValueError) as e:
    print(f"Correctly rejected: {e}")