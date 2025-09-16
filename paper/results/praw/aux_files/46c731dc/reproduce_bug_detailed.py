"""Detailed reproduction showing the objectify bug affects real-world scenarios."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

import praw
from praw.objector import Objector

# Create Reddit instance
reddit = praw.Reddit(
    client_id="test",
    client_secret="test",
    user_agent="test"
)

objector = Objector(reddit)

print("Testing objectify with various data structures that could come from Reddit API:")
print("=" * 70)

# Test 1: Lists of IDs (common in Reddit API responses)
print("\n1. List of comment/post IDs (integers):")
comment_ids = [12345, 67890, 11111]
try:
    result = objector.objectify(comment_ids)
    print(f"   SUCCESS: {comment_ids} -> {result}")
except TypeError as e:
    print(f"   FAILED: {comment_ids}")
    print(f"   Error: {e}")

# Test 2: Mixed list (could be from a bulk response)
print("\n2. Mixed data list:")
mixed_data = ["username1", 42, True, None]
try:
    result = objector.objectify(mixed_data)
    print(f"   SUCCESS: {mixed_data} -> {result}")
except TypeError as e:
    print(f"   FAILED: {mixed_data}")
    print(f"   Error: {e}")

# Test 3: Nested structure with integers
print("\n3. Nested list structure:")
nested = [[1, 2], [3, 4], [5, 6]]
try:
    result = objector.objectify(nested)
    print(f"   SUCCESS: {nested} -> {result}")
except TypeError as e:
    print(f"   FAILED: {nested}")
    print(f"   Error: {e}")

# Test 4: What should work - dict data
print("\n4. Dict data (should work):")
dict_data = {"id": 123, "name": "test"}
try:
    result = objector.objectify(dict_data)
    print(f"   SUCCESS: {dict_data} -> {result}")
except Exception as e:
    print(f"   FAILED: {dict_data}")
    print(f"   Error: {e}")

# Test 5: List of dicts (typical API response)
print("\n5. List of dicts (typical API response):")
api_response = [{"id": 1, "text": "comment1"}, {"id": 2, "text": "comment2"}]
try:
    result = objector.objectify(api_response)
    print(f"   SUCCESS: {api_response} -> {result}")
except Exception as e:
    print(f"   FAILED: {api_response}")
    print(f"   Error: {e}")

print("\n" + "=" * 70)
print("SUMMARY: The objectify method fails on lists containing non-dict primitives.")
print("This is a bug because Reddit API could return lists of IDs, scores, timestamps, etc.")