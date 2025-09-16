#!/usr/bin/env python3
"""
Focused test to check FixedWindowRateLimiter boundary condition
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from limits.strategies import FixedWindowRateLimiter
from limits.storage.memory import MemoryStorage
from limits.limits import RateLimitItemPerSecond

def main():
    print("Testing FixedWindowRateLimiter.test() boundary condition")
    print("="*60)
    
    storage = MemoryStorage()
    strategy = FixedWindowRateLimiter(storage)
    
    # Test case: limit of 5, after using 5, test(cost=1) behavior
    item = RateLimitItemPerSecond(5, 1)
    ids = ('boundary',)
    
    # Clear and use all 5
    strategy.clear(item, *ids)
    for i in range(5):
        success = strategy.hit(item, *ids, cost=1)
        print(f"Hit {i+1}/5: {success}")
    
    # Now we're at the limit
    current = strategy.storage.get(item.key_for(*ids))
    remaining = strategy.get_window_stats(item, *ids).remaining
    print(f"\nState: storage.get()={current}, remaining={remaining}")
    
    # Test if we can hit with cost=1 (should be False)
    can_test = strategy.test(item, *ids, cost=1)
    can_hit = strategy.hit(item, *ids, cost=1)
    
    print(f"\nAt limit (5/5 used):")
    print(f"  test(cost=1) = {can_test}")
    print(f"  hit(cost=1) = {can_hit}")
    
    # Check the formula from line 177
    # return self.storage.get(key) < item.amount - cost + 1
    formula = current < item.amount - 1 + 1
    print(f"\nFormula check:")
    print(f"  storage.get({current}) < amount({item.amount}) - cost(1) + 1")
    print(f"  {current} < {item.amount - 1 + 1}")
    print(f"  {current} < {item.amount}")
    print(f"  Result: {formula}")
    
    # Analyze the bug
    if can_test != can_hit:
        print("\n❌ BUG FOUND!")
        print(f"test() returned {can_test} but hit() returned {can_hit}")
        print("This violates the contract that test() should predict hit() behavior")
        
        # The issue is in line 177 of strategies.py:
        # return self.storage.get(item.key_for(*identifiers)) < item.amount - cost + 1
        # When storage.get() = 5 (all used), amount = 5, cost = 1:
        # 5 < 5 - 1 + 1 = 5 < 5 = False ✓ (correct)
        # But if the formula was wrong...
        
        print("\nDiagnosis:")
        print("The test() method in FixedWindowRateLimiter seems correct.")
        print("Let's check if hit() has issues...")
        
        # Check hit behavior
        strategy.clear(item, *ids)
        for i in range(5):
            strategy.hit(item, *ids, cost=1)
        
        # Check what incr returns
        print(f"\nTrying storage.incr when at limit:")
        incr_result = strategy.storage.incr(
            item.key_for(*ids),
            item.get_expiry(),
            amount=1
        )
        print(f"  incr() returned: {incr_result}")
        print(f"  incr() <= amount: {incr_result} <= {item.amount} = {incr_result <= item.amount}")
        
    elif can_test and can_hit:
        print("\n❌ DIFFERENT BUG FOUND!")
        print("Both test() and hit() returned True when limit was exhausted!")
    else:
        print("\n✅ No bug found - test() and hit() are consistent")
    
    # Additional edge case: cost > remaining
    print("\n" + "="*60)
    print("Testing cost > remaining scenario:")
    
    strategy.clear(item, *ids)
    # Use 3 out of 5
    for i in range(3):
        strategy.hit(item, *ids, cost=1)
    
    current = strategy.storage.get(item.key_for(*ids))
    remaining = strategy.get_window_stats(item, *ids).remaining
    print(f"State: used=3/5, remaining={remaining}")
    
    # Try cost=3 (should fail, only 2 remaining)
    can_test_3 = strategy.test(item, *ids, cost=3)
    can_hit_3 = strategy.hit(item, *ids, cost=3)
    
    print(f"test(cost=3) = {can_test_3} (should be False)")
    print(f"hit(cost=3) = {can_hit_3} (should be False)")
    
    if can_test_3 != can_hit_3:
        print("❌ BUG: test() and hit() disagree!")
    else:
        print("✅ test() and hit() agree")

if __name__ == "__main__":
    main()