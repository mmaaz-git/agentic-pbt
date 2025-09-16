#!/usr/bin/env python3

from blinker import Signal

# Minimal reproduction of the bug
signal = Signal()

def receiver(sender):
    print(f"Received from sender: {sender}")
    
# This should work but crashes with AssertionError
# because sender value 0 collides with ANY_ID which is also 0
try:
    signal.connect(receiver, sender=0)
    print("Successfully connected receiver to sender=0")
    signal.send(0)
except AssertionError as e:
    print(f"Bug reproduced! AssertionError when connecting to sender=0")
    print(f"Error: {e}")
    
# This works fine with any other integer
signal2 = Signal()
signal2.connect(receiver, sender=1)
print("Successfully connected receiver to sender=1")
signal2.send(1)