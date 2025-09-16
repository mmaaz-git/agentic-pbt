#!/usr/bin/env python3
"""Minimal reproduction of SpinnerWindow exception handling bug"""
import sys
import asyncio
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from InquirerPy.containers.spinner import SpinnerWindow
from prompt_toolkit.filters import Condition

async def main():
    # Create a spinner with a redraw that fails
    loading_filter = Condition(lambda: True)
    
    def failing_redraw():
        raise RuntimeError("Redraw failed!")
    
    spinner = SpinnerWindow(
        loading=loading_filter,
        redraw=failing_redraw,
        pattern=["a", "b", "c"],
        delay=0.001
    )
    
    print(f"Initial state: spinner._spinning = {spinner._spinning}")
    
    try:
        await spinner.start()
    except RuntimeError as e:
        print(f"Exception caught: {e}")
    
    print(f"After exception: spinner._spinning = {spinner._spinning}")
    print("BUG: _spinning should be False but remains True")
    
    # Try to restart with a working redraw
    spinner._redraw = lambda: None  # Replace with working redraw
    await spinner.start()
    print("Second start() call returns immediately due to _spinning=True check")

if __name__ == "__main__":
    asyncio.run(main())