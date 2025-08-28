"""Test exception handling in tqdm.gather()."""

import asyncio
from tqdm.asyncio import tqdm_asyncio


async def test_gather_multiple_exceptions():
    """Test that gather properly handles multiple failing tasks."""
    
    async def failing_task(n, delay):
        await asyncio.sleep(delay)
        raise ValueError(f"Task {n} failed")
    
    async def successful_task(n, delay):
        await asyncio.sleep(delay)
        return f"Task {n} success"
    
    # Create mix of failing and successful tasks
    tasks = [
        successful_task(0, 0.01),
        failing_task(1, 0.02),    # Fails second
        successful_task(2, 0.03),
        failing_task(3, 0.001),   # Fails first
        successful_task(4, 0.04),
    ]
    
    try:
        results = await tqdm_asyncio.gather(*tasks, leave=False)
        print(f"Unexpected success with results: {results}")
        assert False, "Should have raised an exception"
    except ValueError as e:
        print(f"Caught exception: {e}")
        # The first exception should be raised
        assert "Task 3 failed" in str(e), f"Wrong exception raised: {e}"
    
    # Wait a bit to see if other exceptions are logged
    await asyncio.sleep(0.1)
    print("Test completed")


async def test_standard_gather_comparison():
    """Compare behavior with standard asyncio.gather."""
    
    async def failing_task(n):
        await asyncio.sleep(0.01 * n)
        raise ValueError(f"Task {n} failed")
    
    print("\n=== Testing standard asyncio.gather ===")
    tasks1 = [failing_task(i) for i in range(3)]
    try:
        results = await asyncio.gather(*tasks1)
        print(f"Unexpected success: {results}")
    except ValueError as e:
        print(f"Standard gather caught: {e}")
    
    await asyncio.sleep(0.1)
    
    print("\n=== Testing tqdm_asyncio.gather ===")
    tasks2 = [failing_task(i) for i in range(3)]
    try:
        results = await tqdm_asyncio.gather(*tasks2, leave=False)
        print(f"Unexpected success: {results}")
    except ValueError as e:
        print(f"tqdm gather caught: {e}")
    
    await asyncio.sleep(0.1)


async def main():
    print("Testing gather exception handling...")
    await test_gather_multiple_exceptions()
    await test_standard_gather_comparison()


if __name__ == "__main__":
    asyncio.run(main())