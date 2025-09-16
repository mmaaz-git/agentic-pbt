import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators

print("Testing boolean validator with floats:")
print(f"boolean(0.0) = {validators.boolean(0.0)}")
print(f"boolean(1.0) = {validators.boolean(1.0)}")

print("\nTesting integer validator with floats:")
print(f"integer(0.0) = {validators.integer(0.0)}")
print(f"integer(1.0) = {validators.integer(1.0)}")
print(f"integer(0.5) = {validators.integer(0.5)}")

print("\nPython equality checks:")
print(f"0.0 == 0: {0.0 == 0}")
print(f"1.0 == 1: {1.0 == 1}")
print(f"0.0 in [0]: {0.0 in [0]}")
print(f"1.0 in [1]: {1.0 in [1]}")