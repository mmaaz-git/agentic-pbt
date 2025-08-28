"""Investigate the CompoundSelect chaining issue."""

from sqlalchemy.future import select
from sqlalchemy import column
import inspect


def investigate_compound_select():
    """Investigate the behavior of set operations and CompoundSelect."""
    
    # Create basic selects
    s1 = select(column('x'))
    s2 = select(column('y'))
    s3 = select(column('z'))
    
    print("=== Initial Select objects ===")
    print(f"s1 type: {type(s1).__name__}")
    print(f"s1 has union: {hasattr(s1, 'union')}")
    print(f"s1 has intersect: {hasattr(s1, 'intersect')}")
    print(f"s1 has except_: {hasattr(s1, 'except_')}")
    
    # Perform union
    union_result = s1.union(s2)
    print(f"\n=== After s1.union(s2) ===")
    print(f"Result type: {type(union_result).__name__}")
    print(f"Result has union: {hasattr(union_result, 'union')}")
    print(f"Result has intersect: {hasattr(union_result, 'intersect')}")
    print(f"Result has except_: {hasattr(union_result, 'except_')}")
    
    # List methods available on CompoundSelect
    print(f"\n=== CompoundSelect methods ===")
    methods = [m for m in dir(union_result) if not m.startswith('_') and callable(getattr(union_result, m, None))]
    print(f"Available methods (first 20): {methods[:20]}")
    
    # Try to chain another union - this should fail
    print(f"\n=== Attempting to chain union ===")
    try:
        chained = union_result.union(s3)
        print(f"Success! Chained type: {type(chained).__name__}")
    except AttributeError as e:
        print(f"Failed with AttributeError: {e}")
    
    # Check if there's an alternative way
    print(f"\n=== Alternative approaches ===")
    
    # Try using select on the union result
    try:
        wrapped = select(union_result)
        print(f"select(union_result) type: {type(wrapped).__name__}")
    except Exception as e:
        print(f"select(union_result) failed: {e}")
    
    # Check parent classes
    print(f"\n=== Class hierarchy ===")
    print(f"Select MRO: {[c.__name__ for c in type(s1).__mro__[:5]]}")
    print(f"CompoundSelect MRO: {[c.__name__ for c in type(union_result).__mro__[:5]]}")
    
    # Check if they share a common interface
    select_methods = set(dir(s1))
    compound_methods = set(dir(union_result))
    missing_in_compound = select_methods - compound_methods
    print(f"\n=== Methods in Select but not in CompoundSelect ===")
    missing_methods = [m for m in missing_in_compound if not m.startswith('_')]
    print(f"Missing methods (first 10): {missing_methods[:10]}")
    
    return union_result


def test_workarounds():
    """Test potential workarounds for the chaining issue."""
    
    s1 = select(column('x'))
    s2 = select(column('y'))
    s3 = select(column('z'))
    
    print("\n=== Testing workarounds ===")
    
    # Workaround 1: Wrap in subquery
    try:
        union12 = s1.union(s2).subquery()
        final = select(union12).union(s3)
        print(f"Workaround 1 (subquery): Success - type {type(final).__name__}")
    except Exception as e:
        print(f"Workaround 1 failed: {e}")
    
    # Workaround 2: Use CTE
    try:
        union12 = s1.union(s2).cte()
        final = select(union12).union(s3)
        print(f"Workaround 2 (CTE): Success - type {type(final).__name__}")
    except Exception as e:
        print(f"Workaround 2 failed: {e}")
    
    # Check documentation claim
    print("\n=== Checking if this is documented behavior ===")
    if s1.union.__doc__:
        print("union() docstring excerpt:")
        print(s1.union.__doc__[:500])


if __name__ == "__main__":
    result = investigate_compound_select()
    test_workarounds()