import sys
import pandas as pd

# Add the site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-pandas_env/lib/python3.13/site-packages/')

from dagster_pandas.constraints import StrictColumnsWithMetadata

# Minimal reproduction of the metadata access issue
required_cols = ['a', 'b']
actual_cols = ['b', 'h']  # Missing 'a', extra 'h'
df = pd.DataFrame(columns=actual_cols)

validator = StrictColumnsWithMetadata(required_cols, enforce_ordering=False, raise_or_typecheck=False)
result = validator.validate(df)

print(f"Validation success: {result.success}")
print(f"Result type: {type(result)}")
print(f"Result attributes: {dir(result)}")

if hasattr(result, 'metadata') and result.metadata:
    print(f"\nMetadata type: {type(result.metadata)}")
    print(f"Metadata content: {result.metadata}")
    
    # Try to access constraint_metadata
    if 'constraint_metadata' in result.metadata:
        constraint_meta = result.metadata['constraint_metadata']
        print(f"\nConstraint metadata type: {type(constraint_meta)}")
        print(f"Constraint metadata: {constraint_meta}")
        
        # The bug: trying to call .get() on JsonMetadataValue
        try:
            actual_meta = constraint_meta.get('actual', {})
            print(f"Actual metadata: {actual_meta}")
        except AttributeError as e:
            print(f"\nERROR: {e}")
            print(f"constraint_meta is of type {type(constraint_meta)}, not a dict!")
            
            # Show how to properly access it
            if hasattr(constraint_meta, 'data'):
                print(f"\nCorrect way - using .data attribute:")
                print(f"constraint_meta.data: {constraint_meta.data}")
                actual_meta = constraint_meta.data.get('actual', {})
                print(f"Actual metadata: {actual_meta}")