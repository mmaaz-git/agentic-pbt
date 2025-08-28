"""Minimal reproduction for quantization range bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')
from coremltools.optimize._utils import get_quant_range

# Bug: When nbits=1 and signed=False, min_val equals max_val
nbits = 1
signed = False
mode = "LINEAR"

min_val, max_val = get_quant_range(nbits, signed, mode)
print(f"nbits={nbits}, signed={signed}, mode={mode}")
print(f"min_val={min_val}, max_val={max_val}")
print(f"Expected: min_val < max_val")
print(f"Actual: min_val={min_val} {'<' if min_val < max_val else '>='} max_val={max_val}")

# Also test LINEAR_SYMMETRIC mode
mode = "LINEAR_SYMMETRIC"
min_val2, max_val2 = get_quant_range(nbits, signed, mode)
print(f"\nnbits={nbits}, signed={signed}, mode={mode}")
print(f"min_val={min_val2}, max_val={max_val2}")
print(f"Expected: min_val < max_val")
print(f"Actual: min_val={min_val2} {'<' if min_val2 < max_val2 else '>='} max_val={max_val2}")

# This breaks the fundamental assumption that quantization should have a range