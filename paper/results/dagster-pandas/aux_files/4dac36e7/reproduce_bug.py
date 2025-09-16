"""Minimal reproduction of the categorical_column bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-pandas_env/lib/python3.13/site-packages')

import pandas as pd
from dagster_pandas.validation import PandasColumn

# Create a simple test DataFrame
df = pd.DataFrame({'category_col': ['A', 'B', 'A', 'C']})

# This should work according to the API but fails
try:
    # PandasColumn.categorical_column expects a list for categories parameter
    cat_col = PandasColumn.categorical_column(
        name='category_col',
        categories=['A', 'B', 'C'],  # Passing a list as shown in examples
        non_nullable=False
    )
    
    # Try to validate
    cat_col.validate(df)
    print("SUCCESS: Validation passed")
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    
    # The error occurs because categorical_column passes the list directly
    # to CategoricalColumnConstraint, which expects a set
    
    # Workaround: Convert to set before passing
    print("\nTrying workaround with set...")
    cat_col_fixed = PandasColumn.categorical_column(
        name='category_col',
        categories={'A', 'B', 'C'},  # Pass a set instead
        non_nullable=False
    )
    cat_col_fixed.validate(df)
    print("WORKAROUND SUCCESS: Validation passed with set")