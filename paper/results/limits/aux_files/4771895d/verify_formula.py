#!/usr/bin/env python3
"""
Verify the test() formula in FixedWindowRateLimiter
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from limits.strategies import FixedWindowRateLimiter
from limits.storage.memory import MemoryStorage
from limits.limits import RateLimitItemPerSecond


def verify_formula():
    """Verify that test() correctly predicts hit() behavior"""
    
    print("Verifying FixedWindowRateLimiter.test() formula")
    print("="*60)
    
    storage = MemoryStorage()
    strategy = FixedWindowRateLimiter(storage)
    
    # Test with limit of 5
    item = RateLimitItemPerSecond(5, 1)
    ids = ('verify',)
    
    test_cases = [
        # (used, cost, should_succeed)
        (0, 1, True),   # 0 used, cost 1 -> should work
        (0, 5, True),   # 0 used, cost 5 -> should work (exactly at limit)
        (0, 6, False),  # 0 used, cost 6 -> should fail (exceeds limit)
        (3, 2, True),   # 3 used, cost 2 -> should work (3+2=5, at limit)
        (3, 3, False),  # 3 used, cost 3 -> should fail (3+3=6, exceeds)
        (4, 1, True),   # 4 used, cost 1 -> should work (4+1=5, at limit)
        (4, 2, False),  # 4 used, cost 2 -> should fail (4+2=6, exceeds)
        (5, 0, True),   # 5 used, cost 0 -> edge case
        (5, 1, False),  # 5 used, cost 1 -> should fail (fully used)
    ]
    
    all_pass = True
    
    for used, cost, expected_success in test_cases:
        # Reset and use 'used' amount
        strategy.clear(item, *ids)
        for _ in range(used):
            strategy.hit(item, *ids, cost=1)
        
        # Get current state
        current = strategy.storage.get(item.key_for(*ids))
        
        # Test both methods
        test_result = strategy.test(item, *ids, cost=cost)
        
        # For hit, we need to be careful not to modify state
        # So let's check what would happen
        if cost == 0:
            # Special case: cost=0 should always succeed if implemented
            hit_would_succeed = True
        else:
            # Check if current + cost <= limit
            hit_would_succeed = (current + cost) <= item.amount
        
        # Verify formula
        formula_result = current < item.amount - cost + 1
        
        print(f"\nCase: used={used}, cost={cost}")
        print(f"  Current count: {current}")
        print(f"  Expected: {expected_success}")
        print(f"  test() returned: {test_result}")
        print(f"  Formula ({current} < {item.amount - cost + 1}): {formula_result}")
        print(f"  Hit would succeed: {hit_would_succeed}")
        
        # Check consistency
        if test_result != hit_would_succeed:
            print(f"  ❌ INCONSISTENCY: test()={test_result}, hit would be {hit_would_succeed}")
            all_pass = False
        elif test_result != expected_success:
            print(f"  ❌ UNEXPECTED: got {test_result}, expected {expected_success}")
            all_pass = False
        else:
            print(f"  ✅ Correct")
    
    print("\n" + "="*60)
    if all_pass:
        print("✅ All cases passed - formula appears correct")
    else:
        print("❌ Some cases failed - there may be a bug")
    
    return all_pass


def test_actual_behavior():
    """Test actual hit() behavior to confirm"""
    
    print("\n\nTesting actual hit() behavior")
    print("="*60)
    
    storage = MemoryStorage()
    strategy = FixedWindowRateLimiter(storage)
    
    item = RateLimitItemPerSecond(5, 1)
    ids = ('actual',)
    
    # Test: use 3, then try to hit with cost=2 (should succeed)
    strategy.clear(item, *ids)
    for _ in range(3):
        strategy.hit(item, *ids, cost=1)
    
    print("After using 3/5:")
    test_2 = strategy.test(item, *ids, cost=2)
    hit_2 = strategy.hit(item, *ids, cost=2)
    print(f"  test(cost=2) = {test_2}")
    print(f"  hit(cost=2) = {hit_2}")
    
    if test_2 != hit_2:
        print("  ❌ BUG: test() and hit() disagree!")
        return False
    
    # Now we should be at 5/5
    current = strategy.storage.get(item.key_for(*ids))
    print(f"\nNow at {current}/5")
    
    # Test: try cost=1 (should fail)
    test_1 = strategy.test(item, *ids, cost=1)
    hit_1 = strategy.hit(item, *ids, cost=1)
    print(f"  test(cost=1) = {test_1}")
    print(f"  hit(cost=1) = {hit_1}")
    
    if test_1 != hit_1:
        print("  ❌ BUG: test() and hit() disagree!")
        return False
    
    print("\n✅ test() and hit() are consistent")
    return True


if __name__ == "__main__":
    verify_formula()
    test_actual_behavior()