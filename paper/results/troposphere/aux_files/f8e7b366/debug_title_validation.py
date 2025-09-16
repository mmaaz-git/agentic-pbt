#!/usr/bin/env python3
"""Debug title validation logic"""

import sys
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

valid_names = re.compile(r"^[a-zA-Z0-9]+$")

def test_condition(title):
    print(f"\nTesting: {repr(title)}")
    print(f"  not title: {not title}")
    if title is not None:
        try:
            match_result = valid_names.match(title)
            print(f"  valid_names.match(title): {match_result}")
            print(f"  not valid_names.match(title): {not match_result}")
        except Exception as e:
            print(f"  valid_names.match(title) raised: {e}")
    
    # Full condition
    if title is not None:
        full_condition = not title or not valid_names.match(title)
        print(f"  Full condition (not title or not match): {full_condition}")

test_condition("")
test_condition(None)
test_condition("Valid123")
test_condition(" ")