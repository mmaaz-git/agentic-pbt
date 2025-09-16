import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

import jurigged.rescript as rescript

# This demonstrates the bug - redirector_code fails with Python keywords
try:
    code_obj = rescript.redirector_code('if')
    print("No error - unexpected!")
except SyntaxError as e:
    print(f"SyntaxError occurred: {e}")
    print("This is a bug - the function should handle keyword names properly")

# Similarly with other keywords
keywords = ['for', 'while', 'class', 'def', 'return', 'if', 'else', 'elif']
for kw in keywords:
    try:
        code_obj = rescript.redirector_code(kw)
        print(f"  {kw}: No error")
    except SyntaxError:
        print(f"  {kw}: SyntaxError - FAILS")