import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/mdxpy_env/lib/python3.13/site-packages')
from mdxpy import normalize

input_str = ']'
normalized_once = normalize(input_str)
normalized_twice = normalize(normalized_once)

print(f"Input: '{input_str}'")
print(f"Normalized once: '{normalized_once}'")
print(f"Normalized twice: '{normalized_twice}'")
print(f"Idempotent? {normalized_once == normalized_twice}")