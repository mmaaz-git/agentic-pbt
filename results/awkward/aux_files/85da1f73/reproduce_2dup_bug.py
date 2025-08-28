import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')
from awkward.forth import ForthMachine64

# Reproduce the 2dup bug
machine = ForthMachine64('10 20 2dup')
machine.begin()
machine.run()

print(f"Input: '10 20 2dup'")
print(f"Actual output: {machine.stack}")
print(f"Expected output: [10, 20, 10, 20]")
print()
print("Bug: '2dup' is parsed as literal '2' instead of the 2dup operation")
print("This affects all 2-prefixed operations like 2swap, 2drop, 2over, etc.")