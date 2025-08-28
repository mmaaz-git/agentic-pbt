import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/spacy-wordnet_env/lib/python3.13/site-packages')

import spacy_wordnet.wordnet_domains as wd
from unittest.mock import mock_open, patch

# Test idempotence - calling load_wordnet_domains multiple times
print("Testing idempotence of load_wordnet_domains...")

# Clear global state
wd.__WN_DOMAINS_BY_SSID.clear()

# Valid test data
test_file_content = """12345678-n\tdomain1 domain2
87654321-v\tdomain3"""

# First load
with patch('builtins.open', mock_open(read_data=test_file_content)):
    wd.load_wordnet_domains()
    
print(f"After first load: {dict(wd.__WN_DOMAINS_BY_SSID)}")
initial_data = dict(wd.__WN_DOMAINS_BY_SSID)

# Second load - should be idempotent
with patch('builtins.open', mock_open(read_data=test_file_content)):
    wd.load_wordnet_domains()
    
print(f"After second load: {dict(wd.__WN_DOMAINS_BY_SSID)}")
after_second = dict(wd.__WN_DOMAINS_BY_SSID)

# Third load
with patch('builtins.open', mock_open(read_data=test_file_content)):
    wd.load_wordnet_domains()
    
print(f"After third load: {dict(wd.__WN_DOMAINS_BY_SSID)}")
after_third = dict(wd.__WN_DOMAINS_BY_SSID)

# Check idempotence
if initial_data == after_second == after_third:
    print("✓ Idempotence works correctly")
else:
    print("✗ Idempotence FAILED")
    
# Check if second/third calls actually skip loading
print("\nChecking if subsequent calls skip file reading...")
wd.__WN_DOMAINS_BY_SSID.clear()

call_count = 0
def counting_open(*args, **kwargs):
    global call_count
    call_count += 1
    return mock_open(read_data=test_file_content)(*args, **kwargs)

with patch('builtins.open', counting_open):
    wd.load_wordnet_domains()
    print(f"Open called after first load: {call_count} times")
    
    wd.load_wordnet_domains()
    print(f"Open called after second load: {call_count} times") 
    
    wd.load_wordnet_domains()
    print(f"Open called after third load: {call_count} times")
    
if call_count == 1:
    print("✓ File only opened once - idempotence optimization works")
else:
    print(f"✗ File opened {call_count} times - idempotence optimization may not work")