#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')
import srsly

# Test case 1: JSON precision loss for large floats
value = 1.5669427390203522e+16
print(f"Original value:  {value}")
print(f"Original repr:   {repr(value)}")

serialized = srsly.json_dumps(value)
print(f"Serialized JSON: {serialized}")

deserialized = srsly.json_loads(serialized)
print(f"Deserialized:    {deserialized}")
print(f"Deserialized repr: {repr(deserialized)}")

print(f"Are they equal? {value == deserialized}")
print(f"Difference: {value - deserialized}")

print("\n---\n")

# Test case 2: Very large float
value2 = 7.4350845423805815e+283
print(f"Original value:  {value2}")
print(f"Original repr:   {repr(value2)}")

serialized2 = srsly.json_dumps(value2)
print(f"Serialized JSON: {serialized2}")

deserialized2 = srsly.json_loads(serialized2)
print(f"Deserialized:    {deserialized2}")
print(f"Deserialized repr: {repr(deserialized2)}")

print(f"Are they equal? {value2 == deserialized2}")
print(f"Difference: {value2 - deserialized2}")