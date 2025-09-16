import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiohttp-retry_env/lib/python3.13/site-packages')

from aiohttp_retry.retry_options import FibonacciRetry

def test_fibonacci_bug():
    """Test for state mutation bug in FibonacciRetry."""
    
    print("=== Testing FibonacciRetry.get_timeout() ===")
    print()
    
    # Create an instance
    retry = FibonacciRetry(multiplier=1.0, max_timeout=100.0)
    
    # The bug: get_timeout() mutates internal state even though
    # the 'attempt' parameter suggests it should be stateless
    
    print("1. Testing repeated calls with same attempt number:")
    val1 = retry.get_timeout(0)
    val2 = retry.get_timeout(0)
    val3 = retry.get_timeout(0)
    
    print(f"   get_timeout(0) call 1: {val1}")
    print(f"   get_timeout(0) call 2: {val2}")
    print(f"   get_timeout(0) call 3: {val3}")
    
    if val1 != val2 or val2 != val3:
        print("   ✗ BUG FOUND: Same attempt number gives different results!")
        print("     This violates the principle that a function should be")
        print("     deterministic for the same inputs.")
        return True
    
    print()
    print("2. Testing sequence generation:")
    
    # Create a fresh instance
    retry2 = FibonacciRetry(multiplier=1.0, max_timeout=100.0)
    
    # Get sequence by calling with increasing attempt numbers
    seq = []
    for i in range(5):
        val = retry2.get_timeout(i)
        seq.append(val)
    
    print(f"   Sequence from attempts 0-4: {seq}")
    
    # Now test if calling with attempt=2 gives the expected value
    retry3 = FibonacciRetry(multiplier=1.0, max_timeout=100.0)
    direct_val = retry3.get_timeout(2)
    
    print(f"   Direct call with attempt=2: {direct_val}")
    print(f"   Expected (3rd Fibonacci):   3.0")
    
    if direct_val != 3.0:
        print("   ✗ BUG FOUND: get_timeout(2) doesn't return 3rd Fibonacci number!")
        print("     The function depends on call history, not just the attempt parameter.")
        return True
    
    print()
    print("3. Looking at the implementation...")
    print()
    print("   The issue is in lines 182-184 of retry_options.py:")
    print("   def get_timeout(self, attempt, response=None):")
    print("       new_current_step = self.prev_step + self.current_step")
    print("       self.prev_step = self.current_step")
    print("       self.current_step = new_current_step")
    print()
    print("   The function modifies self.prev_step and self.current_step")
    print("   but ignores the 'attempt' parameter completely!")
    print()
    
    return False

if __name__ == "__main__":
    if test_fibonacci_bug():
        print("\n🐛 Bug confirmed in FibonacciRetry.get_timeout()")
        print("The method has side effects and doesn't properly use the attempt parameter.")
    else:
        print("\n✅ No obvious bugs found")
        
print("\nExecuting test...")
test_fibonacci_bug()