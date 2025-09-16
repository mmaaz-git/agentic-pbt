import pandas as pd
import numpy as np

# Test whether this can occur in real usage
print("Testing if subnormal floats can occur in real pandas usage:")

# Case 1: Reading from CSV with very small values
import io
csv_data = "value\n0.0\n2.2250738585e-313"
df = pd.read_csv(io.StringIO(csv_data))
print(f"\n1. Reading from CSV: {df['value'].tolist()}")

# Case 2: Mathematical operations that produce subnormal values
x = pd.Series([1.0, 2.0])
y = x * np.finfo(float).tiny / 10
print(f"\n2. Mathematical operations: {y.tolist()}")
print(f"   Are these subnormal? {[val < np.finfo(float).tiny for val in y]}")

# Case 3: User explicitly creates such values
values = [0.0, 2.2250738585e-313]
s = pd.Series(values)
print(f"\n3. User-created Series: {s.tolist()}")

# Now test that qcut fails on these legitimate inputs
print("\n--- Testing qcut on legitimate inputs ---")
for case_name, data in [("CSV data", df['value']), ("Math ops", y), ("User data", s)]:
    try:
        result = pd.qcut(data, q=2, duplicates='drop')
        print(f"{case_name}: SUCCESS - {result.tolist()}")
    except ValueError as e:
        print(f"{case_name}: FAILED - {e}")

# This confirms it's a genuine bug - qcut fails on valid pandas Series
# containing subnormal floats that can arise from legitimate operations