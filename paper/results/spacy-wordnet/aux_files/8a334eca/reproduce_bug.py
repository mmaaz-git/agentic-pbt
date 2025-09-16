import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/spacy-wordnet_env/lib/python3.13/site-packages')

import spacy_wordnet.wordnet_domains as wd
from unittest.mock import mock_open, patch

# Clear global state
wd.__WN_DOMAINS_BY_SSID.clear()

# Test data with an empty line
test_file_content = """12345678-n\tdomain1 domain2
87654321-v\tdomain3

"""

# This will fail with ValueError
print("Testing load_wordnet_domains with empty line in file...")
try:
    with patch('builtins.open', mock_open(read_data=test_file_content)):
        wd.load_wordnet_domains()
    print("SUCCESS: Function handled empty lines")
except ValueError as e:
    print(f"BUG FOUND: {e}")

# Test with line missing tab separator
wd.__WN_DOMAINS_BY_SSID.clear()
test_file_content2 = """12345678-n\tdomain1
invalid_line_without_tab
87654321-v\tdomain3"""

print("\nTesting load_wordnet_domains with line missing tab separator...")
try:
    with patch('builtins.open', mock_open(read_data=test_file_content2)):
        wd.load_wordnet_domains()
    print("SUCCESS: Function handled lines without tabs")
except ValueError as e:
    print(f"BUG FOUND: {e}")