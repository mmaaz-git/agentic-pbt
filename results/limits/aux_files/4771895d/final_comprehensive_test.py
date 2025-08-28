#!/usr/bin/env python3
"""
Final comprehensive test combining all test approaches
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
from limits.strategies import (
    FixedWindowRateLimiter,
    MovingWindowRateLimiter,
    SlidingWindowCounterRateLimiter,
    STRATEGIES
)
from limits.storage.memory import MemoryStorage
from limits.limits import RateLimitItemPerSecond
import traceback


# Core property test
@given(
    limit=st.integers(min_value=1, max_value=50),
    operations=st.lists(
        st.tuples(
            st.sampled_from(['test', 'hit', 'clear']),
            st.integers(min_value=0, max_value=20)  # cost
        ),
        min_size=1,
        max_size=100
    )
)
@settings(max_examples=200, deadline=None)
def test_core_consistency_property(limit, operations):
    """
    Core property: test() should always correctly predict hit() behavior
    """
    storage = MemoryStorage()
    strategies = [
        FixedWindowRateLimiter(storage),
        MovingWindowRateLimiter(storage),
        SlidingWindowCounterRateLimiter(storage)
    ]
    
    item = RateLimitItemPerSecond(limit, 1)
    
    for strategy in strategies:
        name = strategy.__class__.__name__
        ids = (name, str(limit))
        
        strategy.clear(item, *ids)
        
        for i, (op, cost) in enumerate(operations):
            if op == 'clear':
                strategy.clear(item, *ids)
            elif op == 'test':
                # Just test, don't consume
                strategy.test(item, *ids, cost=cost)
            elif op == 'hit':
                # Critical check: test must predict hit
                test_result = strategy.test(item, *ids, cost=cost)
                hit_result = strategy.hit(item, *ids, cost=cost)
                
                if test_result and not hit_result:
                    # BUG FOUND!
                    print(f"\n{'='*70}")
                    print(f"❌ BUG FOUND in {name}!")
                    print(f"{'='*70}")
                    print(f"Limit: {limit}")
                    print(f"After {i} operations")
                    print(f"Operation: hit with cost={cost}")
                    print(f"test() returned: True")
                    print(f"hit() returned: False")
                    
                    # Get diagnostic info
                    stats = strategy.get_window_stats(item, *ids)
                    print(f"\nDiagnostics:")
                    print(f"  Window stats remaining: {stats.remaining}")
                    
                    if isinstance(strategy, FixedWindowRateLimiter):
                        current = strategy.storage.get(item.key_for(*ids))
                        print(f"  Storage count: {current}/{limit}")
                        formula = current < limit - cost + 1
                        print(f"  Test formula: {current} < {limit} - {cost} + 1 = {formula}")
                    
                    # Create reproduction
                    print(f"\nMinimal reproduction:")
                    print(f"```python")
                    print(f"from limits.strategies import {name}")
                    print(f"from limits.storage.memory import MemoryStorage")
                    print(f"from limits.limits import RateLimitItemPerSecond")
                    print(f"")
                    print(f"storage = MemoryStorage()")
                    print(f"strategy = {name}(storage)")
                    print(f"item = RateLimitItemPerSecond({limit}, 1)")
                    print(f"ids = {ids}")
                    print(f"")
                    print(f"# Replay operations:")
                    for j, (prev_op, prev_cost) in enumerate(operations[:i]):
                        if prev_op == 'clear':
                            print(f"strategy.clear(item, *ids)")
                        elif prev_op == 'hit':
                            print(f"strategy.hit(item, *ids, cost={prev_cost})")
                    print(f"")
                    print(f"# This demonstrates the bug:")
                    print(f"assert strategy.test(item, *ids, cost={cost})  # Returns True")
                    print(f"assert strategy.hit(item, *ids, cost={cost})   # Returns False - BUG!")
                    print(f"```")
                    
                    raise AssertionError(f"Bug found: test() returned True but hit() returned False")
                
                elif not test_result and hit_result:
                    # This should never happen
                    print(f"\n{'='*70}")
                    print(f"❌ CRITICAL BUG in {name}!")
                    print(f"{'='*70}")
                    print(f"test() returned False but hit() returned True")
                    print(f"This violates the fundamental contract!")
                    raise AssertionError(f"Critical bug: test() returned False but hit() returned True")


def run_all_tests():
    """Run comprehensive test suite"""
    
    print("="*70)
    print("COMPREHENSIVE BUG HUNT FOR limits.strategies")
    print("="*70)
    
    print("\nRunning property-based consistency test...")
    print("(Testing that test() always correctly predicts hit() behavior)")
    
    try:
        test_core_consistency_property()
        print("✅ All property tests passed - no bugs found!")
        return True
    except AssertionError as e:
        print(f"\n❌ Property test found a bug: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        traceback.print_exc()
        return False


def manual_bug_check():
    """Quick manual check for known edge cases"""
    
    print("\n" + "="*70)
    print("MANUAL EDGE CASE CHECKS")
    print("="*70)
    
    storage = MemoryStorage()
    
    # Check each strategy
    for strategy_name, strategy_class in STRATEGIES.items():
        print(f"\nChecking {strategy_name}...")
        
        strategy = strategy_class(storage)
        item = RateLimitItemPerSecond(5, 1)
        ids = (strategy_name,)
        
        # Edge case 1: Exact limit
        strategy.clear(item, *ids)
        for _ in range(5):
            strategy.hit(item, *ids, cost=1)
        
        test_at_limit = strategy.test(item, *ids, cost=1)
        hit_at_limit = strategy.hit(item, *ids, cost=1)
        
        if test_at_limit != hit_at_limit:
            print(f"  ❌ Bug at limit: test={test_at_limit}, hit={hit_at_limit}")
        else:
            print(f"  ✅ Consistent at limit")
        
        # Edge case 2: Cost = 0
        strategy.clear(item, *ids)
        test_zero = strategy.test(item, *ids, cost=0)
        hit_zero = strategy.hit(item, *ids, cost=0)
        
        if test_zero != hit_zero:
            print(f"  ❌ Bug with cost=0: test={test_zero}, hit={hit_zero}")
        else:
            print(f"  ✅ Consistent with cost=0")
        
        # Edge case 3: Cost > limit
        strategy.clear(item, *ids)
        test_large = strategy.test(item, *ids, cost=10)
        hit_large = strategy.hit(item, *ids, cost=10)
        
        if test_large != hit_large:
            print(f"  ❌ Bug with large cost: test={test_large}, hit={hit_large}")
        else:
            print(f"  ✅ Consistent with large cost")


if __name__ == "__main__":
    print("\n🔍 Starting comprehensive bug hunt for limits.strategies module\n")
    
    # Run manual checks first
    manual_bug_check()
    
    # Run property-based tests
    print("\n")
    bug_found = not run_all_tests()
    
    print("\n" + "="*70)
    if bug_found:
        print("🐛 BUG DETECTED! See details above for reproduction steps.")
    else:
        print("✅ NO BUGS FOUND! All strategies passed consistency tests.")
    print("="*70)