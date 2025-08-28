"""Test more edge cases for get_quant_range"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')
from coremltools.optimize._utils import get_quant_range

print("Testing edge cases for get_quant_range:\n")

# Test various combinations
test_cases = [
    (1, False, "LINEAR"),
    (1, False, "LINEAR_SYMMETRIC"),
    (1, True, "LINEAR"),
    (1, True, "LINEAR_SYMMETRIC"),
    (2, False, "LINEAR_SYMMETRIC"),
    (2, True, "LINEAR_SYMMETRIC"),
]

for nbits, signed, mode in test_cases:
    min_val, max_val = get_quant_range(nbits, signed, mode)
    is_valid = min_val < max_val
    print(f"nbits={nbits}, signed={signed:5}, mode={mode:16} -> [{min_val:3}, {max_val:3}] {'✓' if is_valid else '✗ INVALID!'}")
    
    if not is_valid:
        print(f"  ^ BUG: Range is invalid (min >= max)")
        # Calculate what would happen with this range
        if max_val == min_val:
            print(f"    This would cause division by zero in quantization!")
        print()