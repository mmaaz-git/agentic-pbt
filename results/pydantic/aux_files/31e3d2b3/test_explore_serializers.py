#!/usr/bin/env python3
"""Exploratory script to understand pydantic functional_serializers behavior."""

from typing import Annotated, Any
from pydantic import BaseModel, field_serializer, model_serializer
from pydantic.functional_serializers import PlainSerializer, WrapSerializer, SerializeAsAny
import json

# Test PlainSerializer basic behavior
def custom_serializer(x):
    return f"custom_{x}"

CustomStr = Annotated[str, PlainSerializer(custom_serializer)]

class TestPlainModel(BaseModel):
    value: CustomStr

# Test model
model1 = TestPlainModel(value="test")
print(f"PlainSerializer result: {model1.model_dump()}")
print(f"PlainSerializer JSON: {model1.model_dump_json()}")

# Test WrapSerializer basic behavior  
def wrap_serializer(value, handler, info):
    standard = handler(value)
    return f"wrapped_{standard}"

WrappedStr = Annotated[str, WrapSerializer(wrap_serializer)]

class TestWrapModel(BaseModel):
    value: WrappedStr

model2 = TestWrapModel(value="test")
print(f"WrapSerializer result: {model2.model_dump()}")
print(f"WrapSerializer JSON: {model2.model_dump_json()}")

# Test SerializeAsAny
class Parent(BaseModel):
    x: int

class Child(Parent):
    y: int = 10

# Without SerializeAsAny
parent_var: Parent = Child(x=5)
print(f"Without SerializeAsAny: {parent_var.model_dump()}")

# With SerializeAsAny
any_parent_var: SerializeAsAny[Parent] = Child(x=5)
print(f"With SerializeAsAny: {any_parent_var.model_dump()}")

# Test field_serializer
class FieldSerializerModel(BaseModel):
    numbers: list[int]
    
    @field_serializer('numbers')
    def serialize_numbers(self, value):
        return sorted(value)

model3 = FieldSerializerModel(numbers=[3, 1, 2])
print(f"field_serializer result: {model3.model_dump()}")

# Test model_serializer
class ModelSerializerTest(BaseModel):
    x: int
    y: int
    
    @model_serializer
    def serialize_model(self):
        return {"sum": self.x + self.y}

model4 = ModelSerializerTest(x=5, y=10)
print(f"model_serializer result: {model4.model_dump()}")

# Test when_used parameter
def json_only_serializer(x):
    return f"json_{x}"

JsonOnlyStr = Annotated[str, PlainSerializer(json_only_serializer, when_used='json')]

class JsonOnlyModel(BaseModel):
    value: JsonOnlyStr

model5 = JsonOnlyModel(value="test")
print(f"when_used='json' - Python: {model5.model_dump()}")
print(f"when_used='json' - JSON: {model5.model_dump_json()}")