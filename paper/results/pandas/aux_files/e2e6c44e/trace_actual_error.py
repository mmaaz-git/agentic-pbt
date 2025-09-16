import pandas as pd
import numpy as np
import pandas.core.reshape.tile as tile

# Reproduce with the exact internal flow
values = [0.0, 2.2250738585e-313]
x = pd.Series(values)
q = 2

# Get what _bins_to_cuts produces
try:
    # This mimics what qcut does
    rng = (x.min(), x.max())
    mn, mx = rng
    
    # Calculate edges
    edges = np.linspace(mn, mx, q + 1)
    print(f"Initial edges from linspace: {edges}")
    
    # Now calculate the actual quantiles
    quantiles = np.linspace(0, 1, q + 1)
    print(f"Quantiles: {quantiles}")
    
    # This is what pandas does
    bins = x.quantile(quantiles)
    print(f"Bins from quantile: {bins.values}")
    
    # Check if there's precision loss
    print(f"\nPrecision check:")
    print(f"edges == bins: {np.array_equal(edges, bins.values)}")
    print(f"Difference: {edges - bins.values}")
    
    # Now the actual _bins_to_cuts call
    fac, bins_result = tile._bins_to_cuts(
        x,
        bins=q,
        right=True,
        labels=None,
        include_lowest=False,
        duplicates='drop'
    )
    print(f"Success from _bins_to_cuts")
except Exception as e:
    print(f"Error: {e}")
    
    # Let's check what the issue is more carefully
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # The error happens during interval creation
        # Let's see what the actual breaks are that cause the issue
        print("\n--- Investigating the actual breaks ---")
        
        # This should reproduce the exact flow
        from pandas import Index
        x_idx = Index(x)
        
        # Get the bins
        _, bins_out = tile.cut(
            x_idx,
            bins=q,
            right=True,
            include_lowest=False,
            duplicates='drop',
            retbins=True
        )
        print(f"Bins from cut: {bins_out}")
        
        # Check for warnings
        if w:
            print(f"Warnings during processing: {[str(warning.message) for warning in w]}")