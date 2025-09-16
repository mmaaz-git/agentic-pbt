#!/usr/bin/env python3
"""Demonstrate potential bug in User_Agent when filteredAgents is empty."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

print("Analyzing User_Agent code for potential bug...")
print("="*60)

# Let's analyze the issue in the code
code_snippet = '''
# From cloudscraper/user_agent/__init__.py lines 107-110:

if not self.browser:
    # has to be at least one in there...
    while not filteredAgents.get(self.browser):
        self.browser = random.SystemRandom().choice(list(filteredAgents.keys()))
'''

print("Problematic code:")
print(code_snippet)

print("\nPotential Bug Analysis:")
print("-"*40)
print("""
BUG: If filteredAgents is empty, random.choice() will raise IndexError

The code assumes "has to be at least one in there" but this assumption
might not hold if:
1. A platform has no browsers defined for the desktop/mobile combination
2. The browsers.json file is malformed or incomplete

When filteredAgents is empty:
- list(filteredAgents.keys()) returns []
- random.SystemRandom().choice([]) raises IndexError: Cannot choose from an empty sequence

This would crash the application instead of providing a meaningful error.
""")

print("\nAttempting to reproduce...")
print("-"*40)

# Let's try to create a scenario that would trigger this
import json
import tempfile
import os
from unittest.mock import patch

# Create a browsers.json with an empty section
test_json = {
    "headers": {"chrome": {}, "firefox": {}},
    "cipherSuite": {"chrome": [], "firefox": []},
    "user_agents": {
        "desktop": {
            "windows": {"chrome": ["Mozilla/5.0..."]},
            "linux": {},  # Empty - no browsers
            "darwin": {}   # Empty - no browsers  
        },
        "mobile": {
            "android": {"chrome": ["Mozilla/5.0..."]},
            "ios": {},     # Empty - no browsers
            "linux": {}    # Empty - no browsers
        }
    }
}

# Write to a temp file
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(test_json, f)
    temp_file = f.name

print(f"Created test JSON at: {temp_file}")

# Patch the path to use our test file
original_file = os.path.join(os.path.dirname(__file__), 'browsers.json')

with patch('cloudscraper.user_agent.__file__', __file__):
    with patch('os.path.join') as mock_join:
        def custom_join(*args):
            if 'browsers.json' in args[-1]:
                return temp_file
            return os.path.join(*args)
        
        mock_join.side_effect = custom_join
        
        try:
            from cloudscraper.user_agent import User_Agent
            
            # This should trigger the bug: linux platform with only desktop, no browsers defined
            print("\nTrying to create User_Agent with empty filteredAgents scenario...")
            ua = User_Agent(browser={'platform': 'darwin', 'desktop': True, 'mobile': False})
            print("❌ No error raised - bug might not be triggered in this scenario")
            
        except IndexError as e:
            print(f"✅ BUG CONFIRMED: IndexError raised as expected")
            print(f"   Error: {e}")
        except Exception as e:
            print(f"⚠️  Different error raised: {type(e).__name__}: {e}")
        finally:
            # Clean up
            os.unlink(temp_file)

print("\n" + "="*60)
print("Analysis complete!")