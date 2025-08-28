#!/usr/bin/env python
"""Test for potential bug in timeout handling in FanoutCache._remove."""

import tempfile
import shutil
from unittest.mock import patch, MagicMock
from diskcache import FanoutCache
from diskcache.core import Timeout

def test_timeout_handling_in_remove():
    """Test how _remove handles Timeout exceptions."""
    temp_dir = tempfile.mkdtemp(prefix='test_fanout_')
    cache = FanoutCache(directory=temp_dir, shards=2)
    
    try:
        # Add some items
        for i in range(10):
            cache[f"key_{i}"] = f"value_{i}"
        
        print(f"Added 10 items, cache length: {len(cache)}")
        
        # Mock one shard to raise Timeout
        original_clear = cache._shards[0].clear
        
        def mock_clear(*args, **kwargs):
            # Raise a Timeout exception
            # The FanoutCache._remove expects timeout.args[0] to be a count
            # But typical Timeout exceptions don't have this
            raise Timeout("Database timeout")
        
        cache._shards[0].clear = mock_clear
        
        # Try to clear - this should handle the timeout
        try:
            result = cache.clear(retry=False)
            print(f"Clear returned: {result}")
            
            # The bug is that when Timeout is raised without args[0] being a count,
            # the code will either crash or add wrong values
            print("BUG: Timeout exception handling assumes args[0] is a count!")
            
        except (IndexError, TypeError) as e:
            print(f"CAUGHT EXCEPTION: {e}")
            print("This confirms the bug - Timeout.args[0] is accessed but may not exist")
            return True
            
    finally:
        # Restore
        cache._shards[0].clear = original_clear
        cache.close()
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    return False


def reproduce_timeout_bug():
    """Minimal reproduction of the timeout handling bug."""
    print("Reproducing Timeout handling bug in FanoutCache._remove")
    print("="*60)
    
    # This simulates what happens in _remove when a Timeout is raised
    try:
        timeout = Timeout("Database timeout")  # Standard timeout with message
        count = timeout.args[0]  # This line is in _remove method
        print(f"Count extracted: {count}")
    except IndexError as e:
        print(f"IndexError: {e}")
        print("BUG CONFIRMED: Timeout.args[0] accessed but doesn't exist!")
        return True
    
    return False


def analyze_remove_method():
    """Analyze the _remove method for the bug."""
    print("\nAnalyzing FanoutCache._remove method (lines 480-492):")
    print("-"*60)
    print("""
    def _remove(self, name, args=(), retry=False):
        total = 0
        for shard in self._shards:
            method = getattr(shard, name)
            while True:
                try:
                    count = method(*args, retry=retry)
                    total += count
                except Timeout as timeout:
                    total += timeout.args[0]  # <-- BUG HERE
                else:
                    break
        return total
    """)
    print("\nThe bug: When a Timeout exception is caught, the code assumes")
    print("timeout.args[0] contains a count to add to the total.")
    print("However, standard Timeout exceptions don't have this value,")
    print("leading to an IndexError when accessing args[0].")
    

if __name__ == "__main__":
    print("Testing Timeout exception handling bug...")
    print("="*60)
    
    # First show the analysis
    analyze_remove_method()
    
    # Then reproduce the bug
    print("\n" + "="*60)
    if reproduce_timeout_bug():
        print("\n✓ Bug confirmed in minimal reproduction")
    
    # Try with actual FanoutCache
    print("\n" + "="*60)
    if test_timeout_handling_in_remove():
        print("\n✓ Bug confirmed in FanoutCache test")