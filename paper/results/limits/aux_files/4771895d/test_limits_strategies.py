"""
Property-based tests for limits.strategies module
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
import time

from limits.strategies import (
    FixedWindowRateLimiter,
    MovingWindowRateLimiter,
    SlidingWindowCounterRateLimiter
)
from limits.storage.memory import MemoryStorage
from limits.limits import RateLimitItemPerSecond, RateLimitItemPerMinute


# Strategies for generating test data
@st.composite
def rate_limit_item(draw):
    """Generate a valid RateLimitItem"""
    amount = draw(st.integers(min_value=1, max_value=100))
    multiples = draw(st.integers(min_value=1, max_value=10))
    # Use smaller time windows for faster tests
    limiter_class = draw(st.sampled_from([RateLimitItemPerSecond, RateLimitItemPerMinute]))
    return limiter_class(amount, multiples)


@st.composite  
def identifiers(draw):
    """Generate identifiers for rate limiting"""
    num_ids = draw(st.integers(min_value=0, max_value=3))
    return tuple(draw(st.text(min_size=1, max_size=10)) for _ in range(num_ids))


@st.composite
def cost_value(draw):
    """Generate valid cost values"""
    return draw(st.integers(min_value=1, max_value=50))


def get_all_strategies():
    """Return all rate limiter strategies with memory storage"""
    storage = MemoryStorage()
    return [
        FixedWindowRateLimiter(storage),
        MovingWindowRateLimiter(storage), 
        SlidingWindowCounterRateLimiter(storage)
    ]


# Property 1: Test-Hit Consistency
@given(
    item=rate_limit_item(),
    ids=identifiers(),
    cost=cost_value()
)
@settings(max_examples=100)
def test_test_hit_consistency(item, ids, cost):
    """If test() returns False, then hit() should also return False"""
    for strategy in get_all_strategies():
        # Clear any previous state
        strategy.clear(item, *ids)
        
        # Exhaust the limit first to create a testable scenario
        while strategy.test(item, *ids, cost=1):
            strategy.hit(item, *ids, cost=1)
        
        # Now test the property - if test says no space, hit should fail
        if not strategy.test(item, *ids, cost=cost):
            assert not strategy.hit(item, *ids, cost=cost), \
                f"test() returned False but hit() returned True for {strategy.__class__.__name__}"


# Property 2: Window Stats Consistency  
@given(
    item=rate_limit_item(),
    ids=identifiers(),
    cost=cost_value()
)
@settings(max_examples=100)
def test_window_stats_consistency(item, ids, cost):
    """Window stats remaining should decrease by cost after successful hit"""
    for strategy in get_all_strategies():
        strategy.clear(item, *ids)
        
        # Get initial stats
        initial_stats = strategy.get_window_stats(item, *ids)
        initial_remaining = initial_stats.remaining
        
        # Only test if we have enough space
        assume(cost <= initial_remaining)
        
        # Perform hit
        hit_success = strategy.hit(item, *ids, cost=cost)
        
        if hit_success:
            # Get new stats
            new_stats = strategy.get_window_stats(item, *ids)
            new_remaining = new_stats.remaining
            
            # Check that remaining decreased by cost
            assert new_remaining == initial_remaining - cost, \
                f"Remaining didn't decrease by cost for {strategy.__class__.__name__}: " \
                f"initial={initial_remaining}, new={new_remaining}, cost={cost}"


# Property 3: Clear Reset Property
@given(
    item=rate_limit_item(),
    ids=identifiers(),
    initial_hits=st.lists(cost_value(), min_size=0, max_size=10)
)
@settings(max_examples=100) 
def test_clear_reset_property(item, ids, initial_hits):
    """After clear(), the limit should be fully available"""
    for strategy in get_all_strategies():
        # Do some initial hits
        for cost in initial_hits:
            strategy.hit(item, *ids, cost=cost)
        
        # Clear the limit
        strategy.clear(item, *ids)
        
        # Check that full limit is available
        stats = strategy.get_window_stats(item, *ids)
        assert stats.remaining == item.amount, \
            f"After clear, remaining should be {item.amount} but was {stats.remaining} " \
            f"for {strategy.__class__.__name__}"
        
        # Also verify we can hit up to the full amount
        assert strategy.test(item, *ids, cost=item.amount), \
            f"After clear, should be able to test full amount for {strategy.__class__.__name__}"


# Property 4: Cost Additivity
@given(
    item=rate_limit_item(),
    ids=identifiers(),
    costs=st.lists(st.integers(min_value=1, max_value=10), min_size=2, max_size=5)
)
@settings(max_examples=100)
def test_cost_additivity(item, ids, costs):
    """Multiple hits with smaller costs should be equivalent to one hit with sum"""
    total_cost = sum(costs)
    assume(total_cost <= item.amount)  # Only test within limits
    
    for strategy in get_all_strategies():
        # Test 1: Multiple small hits
        strategy.clear(item, *ids)
        for cost in costs:
            success = strategy.hit(item, *ids, cost=cost)
            assert success, f"Individual hit failed for {strategy.__class__.__name__}"
        
        stats_multiple = strategy.get_window_stats(item, *ids)
        remaining_multiple = stats_multiple.remaining
        
        # Test 2: Single large hit
        strategy.clear(item, *ids)
        success = strategy.hit(item, *ids, cost=total_cost)
        assert success, f"Combined hit failed for {strategy.__class__.__name__}"
        
        stats_single = strategy.get_window_stats(item, *ids)
        remaining_single = stats_single.remaining
        
        # Both should leave the same remaining amount
        assert remaining_multiple == remaining_single, \
            f"Cost additivity violated for {strategy.__class__.__name__}: " \
            f"multiple={remaining_multiple}, single={remaining_single}"


# Property 5: Non-negative Remaining
@given(
    item=rate_limit_item(),
    ids=identifiers(),
    hits=st.lists(cost_value(), min_size=0, max_size=20)
)
@settings(max_examples=100)
def test_non_negative_remaining(item, ids, hits):
    """The remaining count should never be negative"""
    for strategy in get_all_strategies():
        strategy.clear(item, *ids)
        
        for cost in hits:
            strategy.hit(item, *ids, cost=cost)  # May succeed or fail
            
            stats = strategy.get_window_stats(item, *ids)
            assert stats.remaining >= 0, \
                f"Negative remaining count {stats.remaining} for {strategy.__class__.__name__}"


# Property 6: Hit Failure Idempotence
@given(
    item=rate_limit_item(),
    ids=identifiers()
)
@settings(max_examples=100)
def test_hit_failure_idempotence(item, ids):
    """Failed hits should not change the state"""
    for strategy in get_all_strategies():
        strategy.clear(item, *ids)
        
        # Exhaust the limit
        while strategy.hit(item, *ids, cost=1):
            pass
        
        # Get state after exhaustion
        stats_before = strategy.get_window_stats(item, *ids)
        
        # Try to hit again (should fail)
        hit_result = strategy.hit(item, *ids, cost=1)
        assert not hit_result, f"Hit should have failed for {strategy.__class__.__name__}"
        
        # State should be unchanged
        stats_after = strategy.get_window_stats(item, *ids)
        assert stats_before.remaining == stats_after.remaining, \
            f"Failed hit changed state for {strategy.__class__.__name__}"


# Property 7: Test Does Not Modify State  
@given(
    item=rate_limit_item(),
    ids=identifiers(),
    cost=cost_value()
)
@settings(max_examples=100)
def test_test_does_not_modify(item, ids, cost):
    """test() should not modify the rate limit state"""
    for strategy in get_all_strategies():
        strategy.clear(item, *ids)
        
        # Get initial state
        initial_stats = strategy.get_window_stats(item, *ids)
        
        # Call test multiple times
        for _ in range(5):
            strategy.test(item, *ids, cost=cost)
        
        # State should be unchanged
        final_stats = strategy.get_window_stats(item, *ids)
        assert initial_stats.remaining == final_stats.remaining, \
            f"test() modified state for {strategy.__class__.__name__}"


if __name__ == "__main__":
    # Run comprehensive tests
    import traceback
    print("Running property-based tests for limits.strategies...")
    
    tests = [
        ("test_test_hit_consistency", test_test_hit_consistency),
        ("test_window_stats_consistency", test_window_stats_consistency),
        ("test_clear_reset_property", test_clear_reset_property),
        ("test_cost_additivity", test_cost_additivity),
        ("test_non_negative_remaining", test_non_negative_remaining),
        ("test_hit_failure_idempotence", test_hit_failure_idempotence),
        ("test_test_does_not_modify", test_test_does_not_modify)
    ]
    
    failed = []
    for name, test_func in tests:
        try:
            print(f"Running {name}...")
            test_func()
            print(f"  ✓ {name} passed")
        except Exception as e:
            print(f"  ✗ {name} FAILED")
            print(f"    Error: {e}")
            traceback.print_exc()
            failed.append((name, e))
    
    if failed:
        print(f"\n{len(failed)} test(s) failed:")
        for name, error in failed:
            print(f"  - {name}: {error}")
    else:
        print("\nAll tests passed!")