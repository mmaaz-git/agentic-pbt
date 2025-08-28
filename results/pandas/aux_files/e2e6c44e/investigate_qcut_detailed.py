import pandas as pd
import numpy as np

# The issue seems to be with extremely small float values
values = [0.0, 2.2250738585e-313]  

print("Testing pd.qcut with extremely small float")
print(f"Values: {values}")
print(f"Value[1] is subnormal: {values[1] < np.finfo(float).tiny}")
print(f"np.finfo(float).tiny: {np.finfo(float).tiny}")

# Try creating a Series first
s = pd.Series(values)
print(f"\nSeries: {s}")
print(f"Series dtype: {s.dtype}")

# Try to understand what qcut does internally
try:
    # This is what qcut does internally  
    quantiles = np.linspace(0, 1, 2 + 1)
    print(f"\nQuantiles: {quantiles}")
    
    # Get the actual bin edges
    bin_edges = s.quantile(quantiles)
    print(f"Bin edges from quantile: {bin_edges.values}")
    print(f"Bin edges dtype: {bin_edges.dtype}")
    
    # Check for NaN
    print(f"Contains NaN: {np.any(np.isnan(bin_edges))}")
    
    # The issue might be in creating intervals
    from pandas import IntervalIndex
    try:
        ii = IntervalIndex.from_breaks(bin_edges.values, closed='right')
        print(f"IntervalIndex: {ii}")
    except ValueError as e:
        print(f"IntervalIndex creation failed: {e}")
        print(f"Left values: {bin_edges.values[:-1]}")
        print(f"Right values: {bin_edges.values[1:]}")
        print(f"Left has NaN: {np.isnan(bin_edges.values[:-1])}")
        print(f"Right has NaN: {np.isnan(bin_edges.values[1:])}")
        
except Exception as e:
    print(f"Error during manual qcut process: {e}")

# Let's also check if pd.cut has the same issue
print("\n\nTesting pd.cut with same values:")
try:
    cut_result = pd.cut(values, bins=2)
    print(f"pd.cut succeeded: {cut_result}")
except Exception as e:
    print(f"pd.cut failed: {e}")

# Check numeric stability
print(f"\n\nNumeric analysis:")
print(f"values[0] == values[1]: {values[0] == values[1]}")
print(f"np.isclose(values[0], values[1]): {np.isclose(values[0], values[1])}")
print(f"Difference: {values[1] - values[0]}")
print(f"Relative difference: {(values[1] - values[0]) / max(abs(values[0]), abs(values[1]), 1e-308)}")