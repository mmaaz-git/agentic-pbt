"""Minimal reproduction for quantize/dequantize round-trip bug"""

import numpy as np
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')
from coremltools.optimize._utils import quantize_by_scale_and_zp, dequantize_by_scale_and_zp
from coremltools.converters.mil.mil import types

# Minimal failing case from hypothesis
data = np.array([1.0], dtype=np.float32)
nbits = 4
signed = False

# Get the appropriate dtype
dtype_str = f"{'int' if signed else 'uint'}{nbits}"
output_dtype = types.string_to_builtin(dtype_str)

# Create scale
data_range = np.max(data) - np.min(data)
if data_range < 1e-10:
    data_range = 1.0
scale = np.array([data_range / (2**nbits - 1)], dtype=np.float32)

# Use zero_point for unsigned quantization
zero_point = None
if not signed:
    zero_point = np.array([2**(nbits-1)], dtype=types.nptype_from_builtin(output_dtype))

print(f"Original data: {data}")
print(f"Scale: {scale}")
print(f"Zero point: {zero_point}")

# Quantize
quantized = quantize_by_scale_and_zp(data, scale, zero_point, output_dtype)
print(f"Quantized: {quantized}")

# Dequantize
dequantized = dequantize_by_scale_and_zp(quantized, scale, zero_point)
print(f"Dequantized: {dequantized}")

# Check round-trip
max_error = scale[0] * 2
print(f"\nExpected: data ≈ dequantized (within {max_error})")
print(f"Actual difference: {np.abs(data - dequantized)[0]}")
print(f"Are they close? {np.allclose(data, dequantized, atol=max_error, rtol=0.1)}")

# Analyze the issue
print(f"\nAnalysis:")
print(f"When data has no range (constant value), using data_range=1.0 creates wrong scale")
print(f"This causes incorrect quantization/dequantization")