#!/usr/bin/env /root/hypothesis-llm/envs/grpc-stubs_env/bin/python3

import sys
import os
import datetime

# Test the NaN eviction period bug
def test_nan_eviction_bug():
    """Demonstrate that NaN eviction period causes issues."""
    
    # Simulate what happens in _simple_stubs.py lines 51-54
    _EVICTION_PERIOD_KEY = "GRPC_PYTHON_MANAGED_CHANNEL_EVICTION_SECONDS"
    
    # Test 1: NaN value
    os.environ[_EVICTION_PERIOD_KEY] = "nan"
    eviction_seconds = float(os.environ[_EVICTION_PERIOD_KEY])
    print(f"Parsed eviction seconds: {eviction_seconds}")
    print(f"Is NaN: {eviction_seconds != eviction_seconds}")
    
    # This would create a timedelta with NaN seconds
    try:
        _EVICTION_PERIOD = datetime.timedelta(seconds=eviction_seconds)
        print(f"Created timedelta: {_EVICTION_PERIOD}")
        
        # Now simulate what happens when this is used
        now = datetime.datetime.now()
        eviction_time = now + _EVICTION_PERIOD
        print(f"Now: {now}")
        print(f"Eviction time: {eviction_time}")
        
        # Check if eviction_time is valid
        if eviction_time != eviction_time:  # NaN check
            print("BUG: Eviction time is NaN!")
        
        # Try to compare times (as done in line 143 of _simple_stubs.py)
        if eviction_time <= now:
            print("Channel should be evicted")
        else:
            print("Channel should not be evicted")
            
    except (ValueError, TypeError) as e:
        print(f"Error creating timedelta with NaN: {e}")
    
    # Test 2: Negative value
    print("\n--- Testing negative eviction period ---")
    os.environ[_EVICTION_PERIOD_KEY] = "-10"
    eviction_seconds = float(os.environ[_EVICTION_PERIOD_KEY])
    print(f"Parsed eviction seconds: {eviction_seconds}")
    
    _EVICTION_PERIOD = datetime.timedelta(seconds=eviction_seconds)
    print(f"Created timedelta: {_EVICTION_PERIOD}")
    
    now = datetime.datetime.now()
    eviction_time = now + _EVICTION_PERIOD
    print(f"Now: {now}")
    print(f"Eviction time (in the past!): {eviction_time}")
    
    # This means all channels would be immediately evicted
    if eviction_time <= now:
        print("BUG: Channel would be immediately evicted due to negative period!")
    
    # Cleanup
    del os.environ[_EVICTION_PERIOD_KEY]

if __name__ == "__main__":
    test_nan_eviction_bug()