import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.comments as comments

# Test the uniqueness property more carefully
comments_list = ['test', 'test', 'test']  # Same comment 3 times
original_string = "import os"
comment_prefix = "#"

result = comments.add_to_line(comments_list, original_string, False, comment_prefix)
print(f"Comments list: {comments_list}")
print(f"Result: '{result}'")
print(f"Expected: 'import os# test' (comment should appear only once)")

# Test with more complex case
comments_list2 = ['foo', 'bar', 'foo', 'baz', 'bar']
result2 = comments.add_to_line(comments_list2, original_string, False, comment_prefix)
print(f"\nComments list: {comments_list2}")
print(f"Result: '{result2}'")
print(f"Expected: 'import os# foo; bar; baz' (each unique comment once)")