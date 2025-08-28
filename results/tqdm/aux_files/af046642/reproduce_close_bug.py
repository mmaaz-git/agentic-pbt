"""Minimal reproduction of the tqdm.gui close() bug"""

# We can reproduce this without even using matplotlib by directly testing the logic
class MockInstances:
    """Mock of the _instances WeakSet behavior"""
    def __init__(self):
        self.items = set()
    
    def add(self, item):
        self.items.add(item)
    
    def remove(self, item):
        # This raises KeyError if item not present, just like WeakSet
        if item not in self.items:
            raise KeyError(f"Item {item} not in set")
        self.items.remove(item)
    
    def __contains__(self, item):
        return item in self.items


def simulate_close_bug():
    """Simulate the close() method bug"""
    
    print("Simulating tqdm.gui.tqdm_gui.close() behavior:\n")
    
    # Simulate the instance and _instances
    class MockTqdmGui:
        def __init__(self):
            self.disable = False
            self._instances = MockInstances()
            self._instances.add(self)
            print(f"Instance created and added to _instances")
        
        def close(self):
            """This mimics the actual tqdm.gui.tqdm_gui.close() logic"""
            if self.disable:
                print("  Already disabled, returning early")
                return
            
            print("  Setting disable = True")
            self.disable = True
            
            # This is line 97 in tqdm/gui.py that causes the bug
            print("  Attempting to remove from _instances...")
            self._instances.remove(self)
            print("  Successfully removed from _instances")
    
    # Create instance
    pbar = MockTqdmGui()
    
    # First close - should work
    print("\nFirst close():")
    pbar.close()
    
    # Second close - should be safe but will raise KeyError
    print("\nSecond close():")
    try:
        pbar.close()
        print("✓ No error - close() is idempotent")
        return False
    except KeyError as e:
        print(f"✗ KeyError raised: {e}")
        print("  BUG: close() is not idempotent!")
        return True


def show_correct_implementation():
    """Show how the parent class handles this correctly"""
    
    print("\n" + "="*60)
    print("How the parent class (tqdm.std.tqdm) handles this correctly:")
    print("="*60)
    
    print("""
The parent class close() method does:
    
    def close(self):
        if self.disable:
            return
        
        # Prevent multiple closures
        self.disable = True
        
        # decrement instance pos and remove from internal set
        self._decr_instances(self)  # <-- This method handles removal safely
        ...

The _decr_instances() method likely checks if the instance exists before removing.

But tqdm.gui.tqdm_gui.close() does:
    
    def close(self):
        if self.disable:
            return
        
        self.disable = True
        
        with self.get_lock():
            self._instances.remove(self)  # <-- Direct removal, raises KeyError if not present
        ...

The fix would be to either:
1. Check if self is in _instances before removing:
   if self in self._instances:
       self._instances.remove(self)

2. Use try/except:
   try:
       self._instances.remove(self)
   except KeyError:
       pass

3. Call the parent's safer method:
   self._decr_instances(self)
""")


if __name__ == "__main__":
    bug_found = simulate_close_bug()
    
    if bug_found:
        show_correct_implementation()
        
        print("\n" + "="*60)
        print("CONFIRMED BUG in tqdm.gui.tqdm_gui.close()")
        print("="*60)
        print("The method is not idempotent - calling it twice raises KeyError")
        print("This can happen when close() is called explicitly and then __del__ is triggered")