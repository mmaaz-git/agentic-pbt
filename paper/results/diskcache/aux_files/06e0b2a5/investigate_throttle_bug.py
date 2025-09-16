import time
import tempfile

# Import diskcache from the virtual environment
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')
import diskcache
from diskcache.recipes import throttle


def test_throttle_detailed():
    """Detailed investigation of throttle behavior."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        
        call_times = []
        call_count = 0
        
        # Test with 2 calls per 1 second
        @throttle(cache, count=2, seconds=1.0)
        def rate_limited_func():
            nonlocal call_count
            call_count += 1
            call_times.append(time.time())
            print(f"Call {call_count} at time {time.time():.3f}")
        
        print("Testing throttle with count=2, seconds=1.0")
        print("=" * 50)
        
        start_time = time.time()
        
        # Try to make 4 calls
        for i in range(4):
            print(f"\nAttempting call {i+1}...")
            rate_limited_func()
            elapsed = time.time() - start_time
            print(f"Elapsed time after call {i+1}: {elapsed:.3f}s")
        
        print("\n" + "=" * 50)
        print(f"Total calls made: {call_count}")
        print(f"Total elapsed time: {time.time() - start_time:.3f}s")
        
        # Analyze the timing
        print("\nCall timing analysis:")
        for i, t in enumerate(call_times):
            relative_time = t - start_time
            print(f"Call {i+1}: {relative_time:.3f}s from start")
        
        # Count calls in first second
        first_second_calls = sum(1 for t in call_times if t - start_time <= 1.0)
        print(f"\nCalls in first second: {first_second_calls}")
        print(f"Expected calls in first second: 2")
        
        if first_second_calls > 2:
            print(f"\nBUG DETECTED: {first_second_calls} calls were made in the first second, but only 2 should be allowed!")
            return False
        
        return True


def test_throttle_initial_state():
    """Test how throttle initializes its state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        
        # Look at what the throttle decorator does on initialization
        print("\nTesting throttle initialization...")
        print("=" * 50)
        
        @throttle(cache, count=2, seconds=1.0, name='test_func')
        def func():
            return "called"
        
        # Check what's in the cache after decoration
        key = 'test_func'
        value = cache.get(key)
        print(f"Initial cache value for key '{key}': {value}")
        
        # The initial value should be (now, count) according to line 288
        # cache.set(key, (now, count), expire=expire, tag=tag, retry=True)
        if value:
            init_time, init_count = value
            print(f"Initial time: {init_time}")
            print(f"Initial count: {init_count}")
            print(f"This means {init_count} calls are immediately available")
        
        return True


def test_throttle_logic_trace():
    """Trace through the throttle logic to understand the bug."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = diskcache.Cache(tmpdir, eviction_policy='none')
        
        mock_time = 0.0
        sleep_log = []
        
        def mock_time_func():
            return mock_time
        
        def mock_sleep_func(duration):
            nonlocal mock_time
            sleep_log.append(duration)
            mock_time += duration
        
        call_count = 0
        
        @throttle(cache, count=2, seconds=1.0, name='traced_func', 
                 time_func=mock_time_func, sleep_func=mock_sleep_func)
        def traced_func():
            nonlocal call_count
            call_count += 1
            return call_count
        
        print("\nTracing throttle logic with mock time...")
        print("=" * 50)
        print("Configuration: count=2, seconds=1.0 (rate=2.0 calls/second)")
        
        # Make several calls and trace the internal state
        for i in range(5):
            print(f"\n--- Call {i+1} ---")
            print(f"Current mock time: {mock_time:.3f}")
            
            # Get cache state before call
            key = 'traced_func'
            last, tally = cache.get(key)
            print(f"Cache state before: last={last:.3f}, tally={tally:.3f}")
            
            # Calculate what will happen (following the logic in lines 294-304)
            rate = 2.0  # count / seconds = 2 / 1.0
            now = mock_time
            new_tally = tally + (now - last) * rate
            print(f"Calculated new tally: {tally:.3f} + ({now:.3f} - {last:.3f}) * {rate:.3f} = {new_tally:.3f}")
            
            # Make the call
            result = traced_func()
            print(f"Call returned: {result}")
            
            # Check cache state after
            last_after, tally_after = cache.get(key)
            print(f"Cache state after: last={last_after:.3f}, tally={tally_after:.3f}")
            
            if sleep_log and sleep_log[-1] > 0:
                print(f"Sleep was called for {sleep_log[-1]:.3f} seconds")
        
        print(f"\n" + "=" * 50)
        print(f"Total calls made: {call_count}")
        print(f"Final mock time: {mock_time:.3f}")
        
        return True


if __name__ == "__main__":
    print("INVESTIGATING THROTTLE BUG")
    print("=" * 70)
    
    # Run the investigations
    test_throttle_initial_state()
    print("\n" + "=" * 70)
    test_throttle_logic_trace()
    print("\n" + "=" * 70)
    test_throttle_detailed()