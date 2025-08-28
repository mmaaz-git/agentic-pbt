#!/usr/bin/env python3
"""
Comprehensive test for limits.strategies to find bugs
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from limits.strategies import (
    FixedWindowRateLimiter,
    MovingWindowRateLimiter, 
    SlidingWindowCounterRateLimiter
)
from limits.storage.memory import MemoryStorage
from limits.limits import RateLimitItemPerSecond
from hypothesis import given, strategies as st, settings, seed

# Test data strategies
amounts = st.integers(min_value=1, max_value=20)
costs = st.integers(min_value=1, max_value=10)


@given(amount=amounts, hits=st.lists(costs, min_size=0, max_size=30))
@settings(max_examples=50)
@seed(12345)  # For reproducibility
def test_test_hit_consistency_hypothesis(amount, hits):
    """Property: test() should always correctly predict hit() behavior"""
    
    storage = MemoryStorage()
    strategies = [
        FixedWindowRateLimiter(storage),
        MovingWindowRateLimiter(storage),
        SlidingWindowCounterRateLimiter(storage)
    ]
    
    item = RateLimitItemPerSecond(amount, 1)
    
    for strategy in strategies:
        name = strategy.__class__.__name__
        ids = (name, str(amount))  # Unique per strategy
        
        # Clear and replay hits
        strategy.clear(item, *ids)
        
        for i, cost in enumerate(hits):
            # First check what test says
            test_says = strategy.test(item, *ids, cost=cost)
            
            # Then try to hit
            hit_result = strategy.hit(item, *ids, cost=cost)
            
            # They should agree
            if test_says and not hit_result:
                # This is the bug! test() said we could hit but hit() failed
                print(f"\n❌ BUG FOUND in {name}!")
                print(f"  Limit: {amount}")
                print(f"  After {i} hits, tried cost={cost}")
                print(f"  test() returned True but hit() returned False")
                
                # Get diagnostic info
                stats = strategy.get_window_stats(item, *ids)
                print(f"  Window stats: remaining={stats.remaining}")
                
                if isinstance(strategy, FixedWindowRateLimiter):
                    current = strategy.storage.get(item.key_for(*ids))
                    print(f"  Storage count: {current}")
                    print(f"  Test formula: {current} < {amount} - {cost} + 1 = {current < amount - cost + 1}")
                
                # Create minimal reproduction
                print(f"\nMinimal reproduction:")
                print(f"  storage = MemoryStorage()")
                print(f"  strategy = {name}(storage)")
                print(f"  item = RateLimitItemPerSecond({amount}, 1)")
                print(f"  ids = {ids}")
                print(f"  # Replay these hits:")
                for j, c in enumerate(hits[:i]):
                    print(f"  strategy.hit(item, *ids, cost={c})")
                print(f"  # This will show the bug:")
                print(f"  assert strategy.test(item, *ids, cost={cost})")
                print(f"  assert strategy.hit(item, *ids, cost={cost})  # Fails!")
                
                return False
            
            elif not test_says and hit_result:
                # This shouldn't happen - test was conservative but hit succeeded
                print(f"\n❌ OPPOSITE BUG in {name}!")
                print(f"  test() returned False but hit() returned True")
                print(f"  This should never happen!")
                return False
    
    return True


def test_specific_scenarios():
    """Test specific edge cases that might reveal bugs"""
    
    print("Testing specific scenarios...")
    
    scenarios = [
        # (amount, sequence_of_costs, bug_cost)
        (5, [1, 1, 1, 1, 1], 1),  # Exhaust exactly
        (10, [9], 2),  # Almost full, try to exceed
        (3, [1, 1], 1),  # One left
        (1, [], 2),  # Cost exceeds limit
        (100, [50, 49], 2),  # Large numbers
    ]
    
    for amount, costs, final_cost in scenarios:
        storage = MemoryStorage()
        
        for strategy_class in [FixedWindowRateLimiter, MovingWindowRateLimiter, SlidingWindowCounterRateLimiter]:
            strategy = strategy_class(storage)
            name = strategy.__class__.__name__
            
            item = RateLimitItemPerSecond(amount, 1)
            ids = (name, str(amount))
            
            strategy.clear(item, *ids)
            
            # Apply the sequence
            for cost in costs:
                strategy.hit(item, *ids, cost=cost)
            
            # Check consistency
            test_result = strategy.test(item, *ids, cost=final_cost)
            hit_result = strategy.hit(item, *ids, cost=final_cost)
            
            if test_result != hit_result:
                print(f"\n❌ Bug in {name}:")
                print(f"  Scenario: limit={amount}, costs={costs}, final={final_cost}")
                print(f"  test()={test_result}, hit()={hit_result}")
                
                # Debug info
                stats = strategy.get_window_stats(item, *ids)
                print(f"  Remaining: {stats.remaining}")
                
                if isinstance(strategy, FixedWindowRateLimiter):
                    current = strategy.storage.get(item.key_for(*ids))
                    print(f"  Storage: {current}/{amount}")


def test_cost_zero_edge_case():
    """Test behavior with cost=0"""
    
    print("\nTesting cost=0 edge case...")
    
    storage = MemoryStorage()
    strategy = FixedWindowRateLimiter(storage)
    
    item = RateLimitItemPerSecond(5, 1)
    ids = ('zero_cost',)
    
    strategy.clear(item, *ids)
    
    # Use all 5
    for _ in range(5):
        strategy.hit(item, *ids, cost=1)
    
    # Try cost=0
    test_zero = strategy.test(item, *ids, cost=0)
    hit_zero = strategy.hit(item, *ids, cost=0)
    
    print(f"At limit, cost=0:")
    print(f"  test(cost=0) = {test_zero}")
    print(f"  hit(cost=0) = {hit_zero}")
    
    if test_zero != hit_zero:
        print("❌ Bug: test() and hit() disagree on cost=0!")


def main():
    print("Running comprehensive bug hunt for limits.strategies")
    print("="*60)
    
    # Run hypothesis test
    print("\n1. Running property-based tests...")
    try:
        test_test_hit_consistency_hypothesis()
        print("✅ Property tests passed")
    except AssertionError as e:
        print(f"Property test revealed bug: {e}")
    
    # Run specific scenarios
    print("\n2. Testing specific scenarios...")
    test_specific_scenarios()
    
    # Test edge cases
    print("\n3. Testing edge cases...")
    test_cost_zero_edge_case()
    
    print("\n" + "="*60)
    print("Testing complete!")


if __name__ == "__main__":
    main()