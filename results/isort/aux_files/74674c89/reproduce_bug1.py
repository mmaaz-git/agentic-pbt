import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.format as fmt

# Bug 1: Round-trip failure for dotted import statements
import_stmt = "import A.A"
print(f"Original: {import_stmt}")

simplified = fmt.format_simplified(import_stmt)
print(f"Simplified: {simplified}")

restored = fmt.format_natural(simplified)
print(f"Restored: {restored}")

print(f"\nExpected: {import_stmt}")
print(f"Got: {restored}")
print(f"Bug: Round-trip property violated!")