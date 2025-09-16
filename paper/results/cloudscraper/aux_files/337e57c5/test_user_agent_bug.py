#!/usr/bin/env python3
"""Test for potential bug in User_Agent class."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

import json
import os
from unittest.mock import patch, mock_open
from collections import OrderedDict

# Create a minimal mock browsers.json that would cause empty filteredAgents
mock_json_content = json.dumps({
    "user_agents": {
        "desktop": {
            "linux": {},  # Empty - no browsers for linux desktop
            "windows": {"chrome": ["Mozilla/5.0..."]},
        },
        "mobile": {
            "linux": {},  # Empty - no browsers for linux mobile
            "android": {"chrome": ["Mozilla/5.0..."]},
        }
    },
    "headers": {
        "chrome": {
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html",
            "Accept-Language": "en-US",
            "Accept-Encoding": "gzip, deflate"
        }
    },
    "cipherSuite": {
        "chrome": ["TLS_AES_128_GCM_SHA256"]
    }
}, indent=2)

print("Testing User_Agent for potential infinite loop bug...")
print("="*60)

# Monkey-patch the open function to return our mock JSON
with patch('builtins.open', mock_open(read_data=mock_json_content)):
    try:
        from cloudscraper.user_agent import User_Agent
        
        # This should trigger the bug: requesting linux platform with no mobile/desktop preference
        # Since there are no browsers for linux in our mock data, filteredAgents will be empty
        print("\nAttempting to create User_Agent with platform='linux'...")
        print("(This might hang if there's an infinite loop bug)")
        
        # Set a simple test to see if we'd hit the problematic code path
        ua = User_Agent(browser={'platform': 'linux', 'desktop': True, 'mobile': False})
        
        print("✅ User_Agent created successfully (no infinite loop)")
        
    except Exception as e:
        print(f"Exception raised: {e}")
        print("This could indicate the bug exists but manifests differently")

print("\n" + "="*60)
print("Test complete!")

# Now let's analyze the actual code path more carefully
print("\nCode analysis:")
print("-"*40)
print("""
The potential bug is in user_agent/__init__.py lines 107-110:

if not self.browser:
    # has to be at least one in there...
    while not filteredAgents.get(self.browser):
        self.browser = random.SystemRandom().choice(list(filteredAgents.keys()))

Issue: If filteredAgents is empty (no browsers available for the selected platform/device combo),
then filteredAgents.keys() will be empty, causing random.choice() to raise an IndexError.

However, this might not be a bug in practice if the browsers.json file always ensures
at least one browser exists for each platform/device combination.
""")