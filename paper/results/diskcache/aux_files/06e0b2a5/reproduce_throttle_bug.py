import time
import tempfile
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')
import diskcache
from diskcache.recipes import throttle

with tempfile.TemporaryDirectory() as tmpdir:
    cache = diskcache.Cache(tmpdir, eviction_policy='none')
    
    call_times = []
    
    @throttle(cache, count=2, seconds=1.0)
    def rate_limited_func():
        call_times.append(time.time())
    
    start = time.time()
    
    # Make 4 calls
    for i in range(4):
        rate_limited_func()
    
    # Analyze timing
    for i, t in enumerate(call_times):
        print(f"Call {i+1}: {t - start:.3f}s from start")
    
    # Count calls in first second
    calls_in_first_second = sum(1 for t in call_times if t - start <= 1.0)
    
    print(f"\nCalls in first second: {calls_in_first_second}")
    print(f"Expected: 2")
    
    if calls_in_first_second != 2:
        print(f"BUG: throttle allowed {calls_in_first_second} calls in the first second instead of 2")