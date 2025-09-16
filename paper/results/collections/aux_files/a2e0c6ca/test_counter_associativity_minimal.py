import collections

def test_counter_addition_associativity():
    """
    Testing if Counter addition is associative.
    Mathematical associativity: (a + b) + c = a + (b + c)
    """
    # Minimal failing case
    c1 = collections.Counter()           # Empty counter
    c2 = collections.Counter({'x': -1})  # Negative count
    c3 = collections.Counter({'x': 1})   # Positive count
    
    # Left association: (c1 + c2) + c3
    temp1 = c1 + c2  # Counter() since negative counts are dropped
    left = temp1 + c3  # Counter({'x': 1})
    
    # Right association: c1 + (c2 + c3)
    temp2 = c2 + c3  # Counter() since -1 + 1 = 0, which is dropped
    right = c1 + temp2  # Counter()
    
    print(f"c1 = {c1}")
    print(f"c2 = {c2}")
    print(f"c3 = {c3}")
    print(f"\n(c1 + c2) + c3 = {left}")
    print(f"c1 + (c2 + c3) = {right}")
    print(f"\nAssociativity holds? {left == right}")
    
    assert left == right, f"Associativity violated: {left} != {right}"

if __name__ == "__main__":
    try:
        test_counter_addition_associativity()
    except AssertionError as e:
        print(f"\n❌ BUG FOUND: {e}")