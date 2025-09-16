#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

from praw.util import camel_to_snake, snake_case_keys

# Test basic functionality
print("Testing camel_to_snake...")
print(f"'CamelCase' -> '{camel_to_snake('CamelCase')}'")
print(f"'HTTPResponse' -> '{camel_to_snake('HTTPResponse')}'")
print(f"'getHTTPResponseCode' -> '{camel_to_snake('getHTTPResponseCode')}'")

# Test idempotence
test1 = camel_to_snake("TestString")
test2 = camel_to_snake(test1)
print(f"\nIdempotence test: '{test1}' == '{test2}' : {test1 == test2}")

# Test snake_case_keys
d = {"myKey": 1, "anotherKey": 2}
result = snake_case_keys(d)
print(f"\nOriginal dict: {d}")
print(f"Snake case dict: {result}")

# Test collision  
collision_dict = {"myKey": 1, "myKEY": 2}
collision_result = snake_case_keys(collision_dict)
print(f"\nCollision test:")
print(f"Input: {collision_dict}")
print(f"Output: {collision_result}")
print(f"Expected 1 key, got {len(collision_result)} key(s)")