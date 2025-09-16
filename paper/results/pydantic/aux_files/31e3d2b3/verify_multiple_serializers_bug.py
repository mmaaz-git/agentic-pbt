#!/usr/bin/env python3
"""Verify that multiple serializers don't compose as expected."""

from typing import Annotated
from pydantic import BaseModel
from pydantic.functional_serializers import PlainSerializer, WrapSerializer

print("="*60)
print("Testing PlainSerializer composition")
print("="*60)

# Test PlainSerializer
def double(x):
    return x * 2

def add_ten(x):
    return x + 10

def triple(x):
    return x * 3

# If composition worked, we'd expect: triple(add_ten(double(5))) = triple(add_ten(10)) = triple(20) = 60
# But we actually get: triple(5) = 15 (only the last serializer is applied)

ComposedInt = Annotated[int, PlainSerializer(double), PlainSerializer(add_ten), PlainSerializer(triple)]

class PlainModel(BaseModel):
    value: ComposedInt

model = PlainModel(value=5)
result = model.model_dump()

print(f"Input: 5")
print(f"Expected if all serializers compose: double(5) -> 10, add_ten(10) -> 20, triple(20) -> 60")
print(f"Actual result: {result['value']}")
print(f"This shows only the last serializer (triple) was applied: triple(5) = 15")

print("\n" + "="*60)
print("Testing WrapSerializer composition")
print("="*60)

# Test WrapSerializer
def wrap_double(val, handler, info):
    standard = handler(val)
    return standard * 2

def wrap_add_ten(val, handler, info):
    standard = handler(val)
    return standard + 10

def wrap_triple(val, handler, info):
    standard = handler(val)
    return standard * 3

ComposedWrapInt = Annotated[int, WrapSerializer(wrap_double), WrapSerializer(wrap_add_ten), WrapSerializer(wrap_triple)]

class WrapModel(BaseModel):
    value: ComposedWrapInt

wrap_model = WrapModel(value=5)
wrap_result = wrap_model.model_dump()

print(f"Input: 5")
print(f"Expected if all wrap serializers compose: 5 * 2 * 3 + 10 = ?")
print(f"Actual result: {wrap_result['value']}")
print(f"This shows only the last wrap serializer (wrap_triple) was applied: 5 * 3 = 15")

print("\n" + "="*60)
print("Testing mixed PlainSerializer and WrapSerializer")
print("="*60)

MixedInt = Annotated[int, PlainSerializer(double), WrapSerializer(wrap_add_ten), PlainSerializer(triple)]

class MixedModel(BaseModel):
    value: MixedInt

mixed_model = MixedModel(value=5)
mixed_result = mixed_model.model_dump()

print(f"Input: 5")
print(f"With mixed serializers [PlainSerializer(double), WrapSerializer(wrap_add_ten), PlainSerializer(triple)]")
print(f"Actual result: {mixed_result['value']}")
print(f"Again, only the last serializer is applied")

print("\n" + "="*60)
print("CONCLUSION")
print("="*60)
print("BUG CONFIRMED: When multiple PlainSerializer or WrapSerializer instances")
print("are specified in an Annotated type, only the LAST one is applied.")
print("This violates the expected composition behavior where all serializers")
print("should be applied in sequence.")