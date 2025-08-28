"""Test workaround for the CompoundSelect chaining issue."""

from sqlalchemy.future import select
from sqlalchemy import column


def test_workaround_subquery():
    """Test if using subquery as a workaround works."""
    s1 = select(column('a'))
    s2 = select(column('b'))
    s3 = select(column('c'))
    
    # Workaround: wrap intermediate result in subquery
    try:
        intermediate = s1.union(s2).subquery()
        final = select(intermediate).union(s3)
        print(f"Subquery workaround: Works but changes structure")
        print(f"Result type: {type(final).__name__}")
        return True
    except Exception as e:
        print(f"Subquery workaround failed: {e}")
        return False


def test_single_union_multiple_args():
    """Test if union accepts multiple arguments."""
    s1 = select(column('a'))
    s2 = select(column('b'))
    s3 = select(column('c'))
    s4 = select(column('d'))
    
    # Can we pass multiple selects to union at once?
    try:
        result = s1.union(s2, s3, s4)
        print(f"Multiple args to union: Success!")
        print(f"Result type: {type(result).__name__}")
        return True
    except Exception as e:
        print(f"Multiple args failed: {e}")
        return False


if __name__ == "__main__":
    print("=== Testing workarounds ===")
    print("\n1. Subquery workaround:")
    test_workaround_subquery()
    
    print("\n2. Multiple arguments to union:")
    test_single_union_multiple_args()