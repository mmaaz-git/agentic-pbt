"""
Property-based tests for limits.aio module
Testing rate limiting strategies for bugs
"""

import asyncio
import math
from hypothesis import assume, given, settings, strategies as st

# Import the limits module
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

from limits.aio.strategies import (
    FixedWindowRateLimiter,
    MovingWindowRateLimiter,
    SlidingWindowCounterRateLimiter
)
from limits.aio.storage.memory import MemoryStorage
from limits.limits import RateLimitItemPerSecond, RateLimitItemPerMinute


# Test strategies
@st.composite
def rate_limit_item(draw):
    """Generate valid rate limit items"""
    amount = draw(st.integers(min_value=1, max_value=1000))
    multiples = draw(st.integers(min_value=1, max_value=10))
    granularity = draw(st.sampled_from([RateLimitItemPerSecond, RateLimitItemPerMinute]))
    return granularity(amount, multiples)


@st.composite
def identifier_list(draw):
    """Generate valid identifier lists"""
    num_ids = draw(st.integers(min_value=0, max_value=3))
    return [draw(st.text(min_size=1, max_size=10, alphabet=st.characters(categories=['L', 'N']))) 
            for _ in range(num_ids)]


# Property 1: test() and hit() consistency
@given(
    item=rate_limit_item(),
    identifiers=identifier_list(),
    cost=st.integers(min_value=1, max_value=100)
)
@settings(max_examples=200, deadline=None)
async def test_fixed_window_test_hit_consistency(item, identifiers, cost):
    """
    If test() returns True for a cost, hit() should succeed immediately after
    """
    storage = MemoryStorage()
    limiter = FixedWindowRateLimiter(storage)
    
    # Only test when cost is within reasonable bounds
    assume(cost <= item.amount)
    
    can_consume = await limiter.test(item, *identifiers, cost=cost)
    if can_consume:
        # If test says we can consume, hit should succeed
        hit_result = await limiter.hit(item, *identifiers, cost=cost)
        assert hit_result, f"test() returned True but hit() failed for cost={cost}, amount={item.amount}"


# Property 2: Remaining count never negative
@given(
    item=rate_limit_item(),
    identifiers=identifier_list(),
    costs=st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=10)
)
@settings(max_examples=200, deadline=None)
async def test_remaining_never_negative(item, identifiers, costs):
    """
    The remaining count in window stats should never be negative
    """
    storage = MemoryStorage()
    limiter = FixedWindowRateLimiter(storage)
    
    # Consume some of the limit
    for cost in costs:
        await limiter.hit(item, *identifiers, cost=cost)
    
    # Check window stats
    stats = await limiter.get_window_stats(item, *identifiers)
    assert stats.remaining >= 0, f"Remaining count is negative: {stats.remaining}"


# Property 3: Cost boundary validation
@given(
    item=rate_limit_item(),
    identifiers=identifier_list(),
    cost=st.integers(min_value=1, max_value=10000)
)
@settings(max_examples=200, deadline=None) 
async def test_cost_exceeds_limit_always_fails(item, identifiers, cost):
    """
    If cost > limit, both test() and hit() should always return False
    """
    storage = MemoryStorage()
    limiter = FixedWindowRateLimiter(storage)
    
    if cost > item.amount:
        test_result = await limiter.test(item, *identifiers, cost=cost)
        hit_result = await limiter.hit(item, *identifiers, cost=cost)
        
        assert not test_result, f"test() should return False when cost({cost}) > limit({item.amount})"
        assert not hit_result, f"hit() should return False when cost({cost}) > limit({item.amount})"


# Property 4: Fixed window test boundary calculation
@given(
    item=rate_limit_item(),
    identifiers=identifier_list(),
    initial_hits=st.integers(min_value=0, max_value=500),
    test_cost=st.integers(min_value=1, max_value=100)
)
@settings(max_examples=200, deadline=None)
async def test_fixed_window_boundary_calculation(item, identifiers, initial_hits, test_cost):
    """
    Test the boundary calculation in FixedWindowRateLimiter.test()
    The condition is: storage.get(key) < item.amount - cost + 1
    Which is equivalent to: storage.get(key) <= item.amount - cost
    """
    storage = MemoryStorage()
    limiter = FixedWindowRateLimiter(storage)
    
    # Only test valid scenarios
    assume(initial_hits <= item.amount)
    
    # Consume initial hits
    if initial_hits > 0:
        await limiter.hit(item, *identifiers, cost=initial_hits)
    
    # Now test with additional cost
    can_consume = await limiter.test(item, *identifiers, cost=test_cost)
    
    # The test should return True iff: current_count <= amount - cost
    # Which means: current_count + cost <= amount
    expected = (initial_hits + test_cost) <= item.amount
    
    assert can_consume == expected, (
        f"Boundary calculation error: initial={initial_hits}, "
        f"test_cost={test_cost}, amount={item.amount}, "
        f"expected={expected}, got={can_consume}"
    )


# Property 5: Clear operation resets rate limit
@given(
    item=rate_limit_item(),
    identifiers=identifier_list(),
    initial_hits=st.integers(min_value=1, max_value=100)
)
@settings(max_examples=200, deadline=None)
async def test_clear_resets_limit(item, identifiers, initial_hits):
    """
    After clear(), the rate limit should be completely reset
    """
    storage = MemoryStorage()
    limiter = FixedWindowRateLimiter(storage)
    
    # Consume some limit
    consume_amount = min(initial_hits, item.amount)
    if consume_amount > 0:
        await limiter.hit(item, *identifiers, cost=consume_amount)
    
    # Clear the limit
    await limiter.clear(item, *identifiers)
    
    # After clear, we should be able to consume the full amount
    can_consume_full = await limiter.test(item, *identifiers, cost=item.amount)
    assert can_consume_full, "After clear(), should be able to consume full amount"
    
    hit_result = await limiter.hit(item, *identifiers, cost=item.amount)
    assert hit_result, "After clear(), hit() should succeed for full amount"


# Property 6: SlidingWindowCounterRateLimiter weighted count
@given(
    item=rate_limit_item(),
    identifiers=identifier_list(),
    cost=st.integers(min_value=1, max_value=100)
)
@settings(max_examples=100, deadline=None)
async def test_sliding_window_weighted_count(item, identifiers, cost):
    """
    Test weighted count calculation in SlidingWindowCounterRateLimiter
    """
    storage = MemoryStorage()
    limiter = SlidingWindowCounterRateLimiter(storage)
    
    # Only test when cost is within bounds
    assume(cost <= item.amount)
    
    # First hit should always succeed if cost <= amount
    hit_result = await limiter.hit(item, *identifiers, cost=cost)
    assert hit_result, f"First hit failed with cost={cost}, amount={item.amount}"
    
    # Get window stats
    stats = await limiter.get_window_stats(item, *identifiers)
    
    # Remaining should be amount - cost
    expected_remaining = item.amount - cost
    assert stats.remaining == expected_remaining, (
        f"Remaining calculation error: expected {expected_remaining}, got {stats.remaining}"
    )


# Property 7: MovingWindowRateLimiter acquire behavior
@given(
    item=rate_limit_item(),
    identifiers=identifier_list(),
    costs=st.lists(st.integers(min_value=1, max_value=50), min_size=1, max_size=5)
)
@settings(max_examples=100, deadline=None)
async def test_moving_window_acquire_consistency(item, identifiers, costs):
    """
    Test MovingWindowRateLimiter acquisition behavior
    """
    storage = MemoryStorage()
    limiter = MovingWindowRateLimiter(storage)
    
    total_consumed = 0
    for cost in costs:
        if total_consumed + cost <= item.amount:
            result = await limiter.hit(item, *identifiers, cost=cost)
            if result:
                total_consumed += cost
            assert result, f"Hit should succeed when total ({total_consumed + cost}) <= limit ({item.amount})"
        else:
            # Should fail when exceeding limit
            result = await limiter.hit(item, *identifiers, cost=cost)
            assert not result, f"Hit should fail when total ({total_consumed + cost}) > limit ({item.amount})"


# Property 8: Test multiple strategies consistency
@given(
    item=rate_limit_item(),
    identifiers=identifier_list(),
    cost=st.integers(min_value=1, max_value=100)
)
@settings(max_examples=100, deadline=None)
async def test_cross_strategy_first_hit(item, identifiers, cost):
    """
    First hit behavior should be consistent across all strategies
    """
    storages = [MemoryStorage(), MemoryStorage(), MemoryStorage()]
    limiters = [
        FixedWindowRateLimiter(storages[0]),
        MovingWindowRateLimiter(storages[1]),
        SlidingWindowCounterRateLimiter(storages[2])
    ]
    
    # For the first hit, all strategies should behave the same
    # If cost <= amount, it should succeed; otherwise fail
    expected = cost <= item.amount
    
    for limiter, name in zip(limiters, ['Fixed', 'Moving', 'Sliding']):
        result = await limiter.hit(item, *identifiers, cost=cost)
        assert result == expected, (
            f"{name}WindowRateLimiter: expected {expected} for cost={cost}, "
            f"amount={item.amount}, got {result}"
        )


# Runner function for async tests
def run_async_test(test_func):
    """Helper to run async test functions"""
    async def wrapper(*args, **kwargs):
        await test_func(*args, **kwargs)
    
    def sync_wrapper(*args, **kwargs):
        asyncio.run(wrapper(*args, **kwargs))
    
    return sync_wrapper


# Convert async tests to sync for pytest
test_fixed_window_test_hit_consistency = run_async_test(test_fixed_window_test_hit_consistency)
test_remaining_never_negative = run_async_test(test_remaining_never_negative)
test_cost_exceeds_limit_always_fails = run_async_test(test_cost_exceeds_limit_always_fails)
test_fixed_window_boundary_calculation = run_async_test(test_fixed_window_boundary_calculation)
test_clear_resets_limit = run_async_test(test_clear_resets_limit)
test_sliding_window_weighted_count = run_async_test(test_sliding_window_weighted_count)
test_moving_window_acquire_consistency = run_async_test(test_moving_window_acquire_consistency)
test_cross_strategy_first_hit = run_async_test(test_cross_strategy_first_hit)


if __name__ == "__main__":
    print("Running property-based tests for limits.aio...")
    
    # Run each test
    tests = [
        ("test_fixed_window_test_hit_consistency", test_fixed_window_test_hit_consistency),
        ("test_remaining_never_negative", test_remaining_never_negative),
        ("test_cost_exceeds_limit_always_fails", test_cost_exceeds_limit_always_fails),
        ("test_fixed_window_boundary_calculation", test_fixed_window_boundary_calculation),
        ("test_clear_resets_limit", test_clear_resets_limit),
        ("test_sliding_window_weighted_count", test_sliding_window_weighted_count),
        ("test_moving_window_acquire_consistency", test_moving_window_acquire_consistency),
        ("test_cross_strategy_first_hit", test_cross_strategy_first_hit)
    ]
    
    for name, test in tests:
        print(f"\nRunning {name}...")
        try:
            test()
            print(f"✓ {name} passed")
        except Exception as e:
            print(f"✗ {name} failed: {e}")