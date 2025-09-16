"""Minimal reproduction of tqdm.gather() exception handling bug."""

import asyncio
from tqdm.asyncio import tqdm_asyncio


async def reproduce_bug():
    async def task_that_fails(n):
        await asyncio.sleep(0.01 * n)
        raise ValueError(f"Failed task {n}")
    
    # Create multiple failing tasks
    tasks = [task_that_fails(i) for i in range(3)]
    
    print("Testing tqdm_asyncio.gather with multiple exceptions:")
    try:
        await tqdm_asyncio.gather(*tasks, leave=False)
    except ValueError as e:
        print(f"Caught: {e}")
    
    # Give time for warnings to appear
    await asyncio.sleep(0.1)
    print("\nNote: 'Task exception was never retrieved' warnings indicate improper exception handling")


if __name__ == "__main__":
    asyncio.run(reproduce_bug())