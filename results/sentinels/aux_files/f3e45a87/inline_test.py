import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sentinels_env/lib/python3.13/site-packages')

import pickle
from sentinels import Sentinel

# Create initial sentinel
s1 = Sentinel("test")

# Clear registry to simulate edge case
Sentinel._existing_instances.clear()

# Create another sentinel with same name
s2 = Sentinel("test")

# Test if they're the same (they shouldn't be after registry clear)
print(f"s1 is s2: {s1 is s2}")
print(f"s1 id: {id(s1)}, s2 id: {id(s2)}")

# Now test pickle behavior
pickled_s1 = pickle.dumps(s1)
unpickled_s1 = pickle.loads(pickled_s1)

print(f"unpickled_s1 is s1: {unpickled_s1 is s1}")
print(f"unpickled_s1 is s2: {unpickled_s1 is s2}")
print(f"unpickled_s1 id: {id(unpickled_s1)}")

# Edge case: what happens when we pickle s2?
pickled_s2 = pickle.dumps(s2)  
unpickled_s2 = pickle.loads(pickled_s2)

print(f"unpickled_s2 is s2: {unpickled_s2 is s2}")
print(f"unpickled_s2 is s1: {unpickled_s2 is s1}")
print(f"unpickled_s2 is unpickled_s1: {unpickled_s2 is unpickled_s1}")