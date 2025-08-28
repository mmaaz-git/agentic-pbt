import os

sessions_file = "/home/linuxbrew/.linuxbrew/lib/python3.13/site-packages/requests/sessions.py"

with open(sessions_file, 'r') as f:
    lines = f.readlines()

# Find the send method that contains dispatch_hook
in_send_method = False
indent_level = 0
method_start = 0

for i, line in enumerate(lines, 1):
    if 'def send(' in line:
        in_send_method = True
        method_start = i
        print(f"Found send method at line {i}")
        print("Looking for hooks parameter...")
        
    if in_send_method:
        # Look for hooks parameter or assignment
        if 'hooks' in line and not line.strip().startswith('#'):
            print(f"Line {i}: {line.strip()}")
            
        # Check if we've left the method
        if line.strip() and not line[0].isspace() and i > method_start:
            break
            
print("\n" + "="*50)
print("Looking for request method that calls send...")

# Find request method
in_request_method = False
for i, line in enumerate(lines, 1):
    if 'def request(' in line:
        in_request_method = True
        method_start = i
        print(f"Found request method at line {i}")
        
    if in_request_method:
        if 'hooks' in line and not line.strip().startswith('#'):
            print(f"Line {i}: {line.strip()}")
            
        if 'send(' in line:
            print(f"Line {i} (send call): {line.strip()}")
            
        if line.strip() and not line[0].isspace() and i > method_start:
            break