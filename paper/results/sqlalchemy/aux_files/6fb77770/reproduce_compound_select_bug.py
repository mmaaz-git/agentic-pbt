"""Minimal reproduction of the CompoundSelect chaining issue."""

from sqlalchemy.future import select
from sqlalchemy import column


def reproduce_bug():
    """Reproduce the bug where chaining multiple set operations fails."""
    
    # Create three simple selects
    s1 = select(column('a'))
    s2 = select(column('b'))
    s3 = select(column('c'))
    
    # This works - first union
    union_result = s1.union(s2)
    print(f"First union successful: {type(union_result).__name__}")
    
    # This fails - trying to chain another union
    try:
        chained_union = union_result.union(s3)
        print(f"Second union successful: {type(chained_union).__name__}")
    except AttributeError as e:
        print(f"Second union failed: {e}")
        return True  # Bug reproduced
    
    return False  # No bug


def test_expected_behavior():
    """Test what users would reasonably expect to work."""
    
    # Users would expect this pattern to work:
    s1 = select(column('a'))
    s2 = select(column('b'))
    s3 = select(column('c'))
    s4 = select(column('d'))
    
    print("\nExpected pattern: s1.union(s2).union(s3).union(s4)")
    
    try:
        result = s1.union(s2).union(s3).union(s4)
        print(f"Success: Created union of 4 selects")
        return True
    except AttributeError as e:
        print(f"Failed: {e}")
        return False


def test_other_set_operations():
    """Test if the same issue affects intersect and except."""
    
    s1 = select(column('a'))
    s2 = select(column('b'))
    s3 = select(column('c'))
    
    print("\n=== Testing intersect chaining ===")
    try:
        result = s1.intersect(s2).intersect(s3)
        print("Intersect chaining: Success")
    except AttributeError as e:
        print(f"Intersect chaining failed: {e}")
    
    print("\n=== Testing except chaining ===")
    try:
        result = s1.except_(s2).except_(s3)
        print("Except chaining: Success")
    except AttributeError as e:
        print(f"Except chaining failed: {e}")
    
    print("\n=== Testing mixed operations ===")
    try:
        result = s1.union(s2).intersect(s3)
        print("Mixed operations: Success")
    except AttributeError as e:
        print(f"Mixed operations failed: {e}")


if __name__ == "__main__":
    print("=== Reproducing the bug ===")
    bug_found = reproduce_bug()
    
    if bug_found:
        print("\n✗ BUG CONFIRMED: Cannot chain multiple set operations")
        test_expected_behavior()
        test_other_set_operations()
    else:
        print("\n✓ No bug found")