import os
import re

# Search for dispatch_hook usage in the requests directory
requests_dir = "/home/linuxbrew/.linuxbrew/lib/python3.13/site-packages/requests"

print("Searching for dispatch_hook usage...")
for filename in os.listdir(requests_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(requests_dir, filename)
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                if 'dispatch_hook' in content:
                    print(f"\nFound in {filename}:")
                    # Find lines containing dispatch_hook
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'dispatch_hook' in line:
                            # Print context around the line
                            start = max(0, i-1)
                            end = min(len(lines), i+2)
                            for j in range(start, end):
                                print(f"  {j+1}: {lines[j]}")
        except:
            pass

print("\n" + "="*50)
print("Searching for default_hooks usage...")
for filename in os.listdir(requests_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(requests_dir, filename)
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                if 'default_hooks' in content:
                    print(f"\nFound in {filename}:")
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'default_hooks' in line:
                            start = max(0, i-1)
                            end = min(len(lines), i+2)
                            for j in range(start, end):
                                print(f"  {j+1}: {lines[j]}")
        except:
            pass