#!/usr/bin/env python3
"""Test to understand how multiple serializers are handled."""

from typing import Annotated
from pydantic import BaseModel
from pydantic.functional_serializers import PlainSerializer

def transform_a(x):
    result = f"A({x})"
    print(f"transform_a: {x} -> {result}")
    return result

def transform_b(x):
    result = f"B({x})"
    print(f"transform_b: {x} -> {result}")
    return result

def transform_c(x):
    result = f"C({x})"
    print(f"transform_c: {x} -> {result}")
    return result

# Test with three serializers
print("Testing with three PlainSerializers in order A, B, C:")
TripleTransform = Annotated[str, PlainSerializer(transform_a), PlainSerializer(transform_b), PlainSerializer(transform_c)]

class Model1(BaseModel):
    field: TripleTransform

model1 = Model1(field="input")
result1 = model1.model_dump()
print(f"Result: {result1['field']}")
print()

# Test with different order
print("Testing with three PlainSerializers in order C, B, A:")
TripleTransform2 = Annotated[str, PlainSerializer(transform_c), PlainSerializer(transform_b), PlainSerializer(transform_a)]

class Model2(BaseModel):
    field: TripleTransform2

model2 = Model2(field="input")
result2 = model2.model_dump()
print(f"Result: {result2['field']}")
print()

# Test with just one
print("Testing with just one PlainSerializer (B):")
SingleTransform = Annotated[str, PlainSerializer(transform_b)]

class Model3(BaseModel):
    field: SingleTransform

model3 = Model3(field="input")
result3 = model3.model_dump()
print(f"Result: {result3['field']}")
print()

# What if we check the schema?
print("Checking the core schema for TripleTransform:")
from pydantic._internal._core_utils import get_pydantic_metadata
metadata = get_pydantic_metadata(TripleTransform)
print(f"Number of metadata items: {len(metadata) if metadata else 0}")
if metadata:
    for i, item in enumerate(metadata):
        print(f"  Item {i}: {type(item).__name__}")