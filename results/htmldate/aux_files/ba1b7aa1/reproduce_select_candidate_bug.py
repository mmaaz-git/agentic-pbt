#!/usr/bin/env /root/hypothesis-llm/envs/htmldate_env/bin/python
"""Minimal reproduction of IndexError in select_candidate function"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

import re
from collections import Counter
from datetime import datetime
from htmldate.core import select_candidate
from htmldate.utils import Extractor

# Minimal failing input from Hypothesis
occurrences = Counter({'0': 1, '00': 2})

# Setup the patterns
catch = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
yearpat = re.compile(r'(\d{4})')

# Setup options
options = Extractor(
    False,  # extensive_search
    datetime(2030, 12, 31),  # max_date
    datetime(2000, 1, 1),  # min_date
    True,  # original_date
    "%Y-%m-%d"  # outputformat
)

print("Testing select_candidate with occurrences:", dict(occurrences))
print("This should cause an IndexError...")

try:
    result = select_candidate(occurrences, catch, yearpat, options)
    print("Result:", result)
except IndexError as e:
    print(f"IndexError occurred: {e}")
    print("\nThis happens at line 397 in htmldate/core.py:")
    print("    elif years[1] != years[0] and counts[1] / counts[0] > 0.5:")
    print("When there are fewer than 2 valid year patterns, accessing years[1] fails.")
    import traceback
    traceback.print_exc()