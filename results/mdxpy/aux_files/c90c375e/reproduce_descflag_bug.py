import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/mdxpy_env/lib/python3.13/site-packages')
from mdxpy.mdx import DescFlag

# Check all the enum values
print("DescFlag members:")
for member in DescFlag:
    print(f"  {member.name} = {member.value}")

# Try to parse "BEFORE_AND_AFTER" with underscores removed 
test_values = ["BEFORE_AND_AFTER", "before_and_after", "beforeandafter", "BEFOREANDAFTER"]

for value in test_values:
    try:
        result = DescFlag(value)
        print(f"✓ DescFlag('{value}') = {result.name}")
    except ValueError as e:
        print(f"✗ DescFlag('{value}') failed: {e}")