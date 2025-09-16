"""Property-based tests for tqdm.asyncio module."""

import asyncio
import random
from hypothesis import given, strategies as st, settings, assume
from tqdm.asyncio import tqdm_asyncio, tqdm


@given(st.lists(st.integers(), min_size=1, max_size=20))
@settings(max_examples=100, deadline=5000)
def test_gather_order_preservation(values):
    """Test that tqdm.gather() preserves order of results."""
    
    async def create_task(value, delay):
        await asyncio.sleep(delay)
        return value
    
    async def run_test():
        # Create tasks with random delays to ensure order preservation isn't accidental
        delays = [random.uniform(0, 0.01) for _ in values]
        tasks = [create_task(val, delay) for val, delay in zip(values, delays)]
        
        # Use tqdm.gather to collect results
        results = await tqdm_asyncio.gather(*tasks, total=len(values), leave=False)
        
        # Results should match input order exactly
        assert results == values, f"Order not preserved: expected {values}, got {results}"
    
    asyncio.run(run_test())


@given(st.lists(st.integers(), min_size=1, max_size=10))
@settings(max_examples=100, deadline=5000)
def test_as_completed_count(values):
    """Test that as_completed yields exactly the expected number of items."""
    
    async def create_task(value):
        await asyncio.sleep(0.001)
        return value
    
    async def run_test():
        tasks = [create_task(val) for val in values]
        
        # Count items yielded by as_completed
        count = 0
        results = []
        for fut in tqdm_asyncio.as_completed(tasks, total=len(values), leave=False):
            result = await fut
            results.append(result)
            count += 1
        
        # Should yield exactly len(values) items
        assert count == len(values), f"Expected {len(values)} items, got {count}"
        # All values should be present (though order may differ)
        assert sorted(results) == sorted(values), f"Missing values: expected {sorted(values)}, got {sorted(results)}"
    
    asyncio.run(run_test())


@given(st.lists(st.integers(), max_size=20))
@settings(max_examples=100)
def test_async_iteration_completeness(values):
    """Test that async iteration processes all items."""
    
    async def run_test():
        collected = []
        
        # Use tqdm_asyncio to iterate through async generator
        async def async_gen():
            for val in values:
                await asyncio.sleep(0)
                yield val
        
        async for item in tqdm_asyncio(async_gen(), total=len(values), leave=False):
            collected.append(item)
        
        assert collected == values, f"Not all items processed: expected {values}, got {collected}"
    
    asyncio.run(run_test())


@given(st.lists(st.integers(min_value=0, max_value=10), min_size=1, max_size=10))
@settings(max_examples=100)
def test_exception_handling_closes_bar(values):
    """Test that progress bar properly closes on exceptions."""
    
    async def run_test():
        # Pick a random position to raise exception
        exception_pos = random.randint(0, len(values) - 1)
        
        async def async_gen_with_exception():
            for i, val in enumerate(values):
                if i == exception_pos:
                    raise ValueError(f"Test exception at position {i}")
                await asyncio.sleep(0)
                yield val
        
        bar = tqdm_asyncio(async_gen_with_exception(), total=len(values), leave=False)
        collected = []
        
        try:
            async for item in bar:
                collected.append(item)
        except ValueError:
            # Check that the bar was closed
            assert bar.n <= len(values), "Progress bar counter exceeded total"
            # The disable flag should be set when closed
            if hasattr(bar, 'disable'):
                assert bar.disable or bar.n == bar.total, "Bar not properly closed on exception"
        else:
            # Should have raised an exception
            assert False, "Expected ValueError but none was raised"
        
        # Should have collected items up to exception point
        assert len(collected) == exception_pos, f"Collected {len(collected)} items, expected {exception_pos}"
    
    asyncio.run(run_test())


@given(st.lists(st.integers(), min_size=2, max_size=10))
@settings(max_examples=50, deadline=5000)
def test_gather_with_exceptions(values):
    """Test gather behavior when some tasks fail."""
    
    async def create_task(value):
        if value < 0:
            raise ValueError(f"Negative value: {value}")
        await asyncio.sleep(0.001)
        return value
    
    async def run_test():
        # Mix positive and negative values
        mixed_values = values[:len(values)//2] + [-1] + values[len(values)//2:]
        tasks = [create_task(val) for val in mixed_values]
        
        try:
            results = await tqdm_asyncio.gather(*tasks, total=len(tasks), leave=False)
            # Should have raised if there were negative values
            assert all(v >= 0 for v in mixed_values), "Should have raised ValueError for negative values"
        except ValueError:
            # Expected for negative values
            assert any(v < 0 for v in mixed_values), "ValueError raised but no negative values"
    
    asyncio.run(run_test())


@given(st.integers(min_value=0, max_value=100))
@settings(max_examples=100)
def test_empty_iteration(total_value):
    """Test behavior with empty iterables."""
    
    async def run_test():
        # Test with empty async generator
        async def empty_gen():
            return
            yield  # Never reached
        
        collected = []
        async for item in tqdm_asyncio(empty_gen(), total=total_value, leave=False):
            collected.append(item)
        
        assert collected == [], f"Expected empty list, got {collected}"
        
        # Test with empty list
        collected2 = []
        async for item in tqdm_asyncio([], total=0, leave=False):
            collected2.append(item)
        
        assert collected2 == [], f"Expected empty list, got {collected2}"
    
    asyncio.run(run_test())