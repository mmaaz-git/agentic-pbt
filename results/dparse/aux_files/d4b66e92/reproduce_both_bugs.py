#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

from dparse.updater import RequirementsTXTUpdater
from dparse.dependencies import Dependency

print("=" * 60)
print("BUG 1: Whitespace before comments not preserved correctly")
print("=" * 60)

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
print(f"Original: 'A==0' + {repr(whitespace)} + '# '")

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
    print(f"Result: 'A==0' + {repr(result_whitespace)} + '# '")

# Check if whitespace is preserved
if whitespace == result_whitespace:
    print("✓ Whitespace preserved correctly")
else:
    print("✗ BUG CONFIRMED: Whitespace order reversed!")
    print(f"  Input whitespace:  {repr(whitespace)}")
    print(f"  Output whitespace: {repr(result_whitespace)}")

print("\n" + "=" * 60)
print("BUG 2: Environment markers with trailing spaces not preserved")
print("=" * 60)

# Test case 2: Environment marker with trailing space
name2 = 'A'
old_version2 = '0' 
new_version2 = '0'
env_marker2 = ' '  # Just a space

line2 = f"{name2}=={old_version2}; {env_marker2}"
content2 = line2

print(f"Original line: {repr(line2)}")

# Create dependency
dep2 = Dependency(
    name=name2,
    specs=f"=={old_version2}",
    line=line2,
    extras=[]
)

# Update requirement
result2 = RequirementsTXTUpdater.update(content2, dep2, new_version2)

print(f"Result line: {repr(result2)}")

# Check if environment marker is preserved
if f"; {env_marker2}" in result2:
    print("✓ Environment marker with space preserved")
else:
    print("✗ BUG CONFIRMED: Environment marker trailing space lost!")
    print(f"  Expected to contain: {repr(f'; {env_marker2}')}")
    print(f"  Actually got: {repr(result2)}")