#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

from dparse.updater import RequirementsTXTUpdater
from dparse.dependencies import Dependency

# Test case from Hypothesis
name = 'A'
old_version = '0'
new_version = '0'
comment = ''
whitespace = ' \t'  # space followed by tab

# Create requirement line with specific whitespace before comment
line = f"{name}=={old_version}{whitespace}# {comment}"
content = line

print(f"Original line: {repr(line)}")
print(f"Whitespace before comment (repr): {repr(whitespace)}")

# Create dependency
dep = Dependency(
    name=name,
    specs=f"=={old_version}",
    line=line,
    extras=[]
)

# Update requirement
result = RequirementsTXTUpdater.update(content, dep, new_version)

print(f"Result line: {repr(result)}")

# Extract whitespace from result
import re
match = re.search(r'A==0(.*)#', result)
if match:
    result_whitespace = match.group(1)
    print(f"Result whitespace before comment (repr): {repr(result_whitespace)}")

# Check if whitespace is preserved
if whitespace + f"# {comment}" in result:
    print("✓ Whitespace preserved correctly")
else:
    print("✗ BUG: Whitespace not preserved correctly!")
    print(f"  Expected: {repr(whitespace + f'# {comment}')}")
    print(f"  Got in result: {repr(result)}")