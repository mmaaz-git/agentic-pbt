"""
Analysis: Is Counter addition's lack of associativity a bug?

The collections.Counter class implements multiset operations where the + operator
is documented to "only include positive counts" in the result.

However, this design choice breaks a fundamental mathematical property - associativity.
For any proper addition operation, (a + b) + c should equal a + (b + c).

The problem occurs when:
1. Counters can have negative counts (allowed by design)
2. Addition drops non-positive results
3. This dropping happens at different stages depending on grouping

This is arguably a CONTRACT bug - the documentation suggests Counter implements
multiset operations, but doesn't warn that basic algebraic properties like
associativity don't hold when negative counts are involved.
"""

import collections

def demonstrate_broken_associativity():
    """Show multiple cases where associativity fails"""
    
    test_cases = [
        # Case 1: Empty counter with negatives
        (collections.Counter(), collections.Counter({'x': -1}), collections.Counter({'x': 1})),
        
        # Case 2: Multiple keys affected
        (collections.Counter({'a': 1}), collections.Counter({'a': -2, 'b': -1}), collections.Counter({'a': 1, 'b': 1})),
        
        # Case 3: Larger negative values
        (collections.Counter({'k': 5}), collections.Counter({'k': -10}), collections.Counter({'k': 5})),
    ]
    
    failures = []
    
    for i, (c1, c2, c3) in enumerate(test_cases, 1):
        left = (c1 + c2) + c3
        right = c1 + (c2 + c3)
        
        if left != right:
            failures.append({
                'case': i,
                'c1': dict(c1),
                'c2': dict(c2),
                'c3': dict(c3),
                'left': dict(left),
                'right': dict(right)
            })
    
    return failures

if __name__ == "__main__":
    failures = demonstrate_broken_associativity()
    
    print("Counter Addition Associativity Failures:")
    print("=" * 50)
    
    for failure in failures:
        print(f"\nCase {failure['case']}:")
        print(f"  c1 = {failure['c1']}")
        print(f"  c2 = {failure['c2']}")
        print(f"  c3 = {failure['c3']}")
        print(f"  (c1 + c2) + c3 = {failure['left']}")
        print(f"  c1 + (c2 + c3) = {failure['right']}")
    
    print("\n" + "=" * 50)
    print(f"Total failures: {len(failures)} out of 3 test cases")
    print("\nConclusion: Counter's + operator violates associativity when negative counts are present.")