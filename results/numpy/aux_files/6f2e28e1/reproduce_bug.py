"""Reproduce whitespace field name bug in numpy.rec.format_parser"""

import numpy.rec as rec

# Bug: Different whitespace-only field names become duplicates after stripping
formats = ['i4', 'f8']
names = [' ', '\t']  # Two different whitespace strings

try:
    parser = rec.format_parser(formats, names=names, titles=None)
    print("No error - unexpected!")
except ValueError as e:
    print(f"ValueError raised: {e}")
    print()
    print("Problem: The input names [' ', '\\t'] are different strings")
    print("But after stripping, both become '', causing a duplicate field name error")
    print("This prevents valid use cases with whitespace field names")