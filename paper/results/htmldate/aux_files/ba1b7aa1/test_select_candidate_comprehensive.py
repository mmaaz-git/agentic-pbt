#!/usr/bin/env /root/hypothesis-llm/envs/htmldate_env/bin/python
"""Comprehensive test of the select_candidate bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

import re
from collections import Counter
from datetime import datetime
from htmldate.core import select_candidate
from htmldate.utils import Extractor

def test_case(occurrences_dict, description):
    """Test a specific case"""
    print(f"\n{description}")
    print(f"Input: {occurrences_dict}")
    
    occurrences = Counter(occurrences_dict)
    catch = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
    yearpat = re.compile(r'(\d{4})')
    
    options = Extractor(
        False,  # extensive_search
        datetime(2030, 12, 31),  # max_date
        datetime(2000, 1, 1),  # min_date
        True,  # original_date
        "%Y-%m-%d"  # outputformat
    )
    
    try:
        result = select_candidate(occurrences, catch, yearpat, options)
        print(f"Result: {result}")
    except IndexError as e:
        print(f"❌ IndexError: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    print("✓ Passed")
    return True

# Test various cases
print("Testing select_candidate with various inputs...")

# Case 1: Original bug - patterns without valid years
test_case({'0': 1, '00': 2}, "Case 1: Patterns without 4-digit years")

# Case 2: Single pattern without valid year
test_case({'99': 5}, "Case 2: Single pattern, no valid year") 

# Case 3: Multiple patterns without valid years
test_case({'1': 3, '22': 4, '333': 5}, "Case 3: Multiple patterns, no valid years")

# Case 4: One valid year pattern (edge case)
test_case({'2021': 3, 'abc': 2}, "Case 4: One pattern with year, one without")

# Case 5: Valid case with proper date patterns (should work)
test_case({'2021-01-01': 3, '2022-06-15': 2}, "Case 5: Valid date patterns (control)")

# Additional edge cases
test_case({}, "Case 6: Empty occurrences")
test_case({'': 1}, "Case 7: Empty string pattern")

print("\n" + "="*50)
print("Bug Summary:")
print("The select_candidate function fails when:")
print("1. Input patterns don't contain valid 4-digit years")
print("2. Only one pattern contains a valid year")
print("3. The years list has fewer than 2 elements")
print("This causes IndexError when accessing years[0] or years[1]")