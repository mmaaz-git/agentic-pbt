#!/usr/bin/env python3
"""Minimal reproduction of PlainSerializer composition issue."""

from typing import Annotated
from pydantic import BaseModel
from pydantic.functional_serializers import PlainSerializer

# Test case that failed: value=1, multiplier=2
value = 1
multiplier = 2

def multiply(x):
    print(f"multiply called with {x}, returning {x * multiplier}")
    return x * multiplier

def add_one(x):
    print(f"add_one called with {x}, returning {x + 1}")
    return x + 1

# Apply two transformations
TransformedInt = Annotated[int, PlainSerializer(multiply), PlainSerializer(add_one)]

class Model(BaseModel):
    field: TransformedInt

model = Model(field=value)
result = model.model_dump()

print(f"\nInput value: {value}")
print(f"Multiplier: {multiplier}")
print(f"Result: {result['field']}")
print(f"Expected (value * multiplier) + 1 = ({value} * {multiplier}) + 1 = {(value * multiplier) + 1}")
print(f"Actual result: {result['field']}")

# Let's also test the reverse order
TransformedInt2 = Annotated[int, PlainSerializer(add_one), PlainSerializer(multiply)]

class Model2(BaseModel):
    field: TransformedInt2

model2 = Model2(field=value)
result2 = model2.model_dump()

print(f"\nReversed order:")
print(f"Result: {result2['field']}")
print(f"Expected (value + 1) * multiplier = ({value} + 1) * {multiplier} = {(value + 1) * multiplier}")