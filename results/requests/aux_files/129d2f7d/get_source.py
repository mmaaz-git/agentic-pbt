import requests.hooks
import inspect

print("="*50)
print("HOOKS constant:")
print(requests.hooks.HOOKS)

print("\n" + "="*50)
print("Source code for default_hooks:")
print(inspect.getsource(requests.hooks.default_hooks))

print("\n" + "="*50)
print("Source code for dispatch_hook:")
print(inspect.getsource(requests.hooks.dispatch_hook))

# Let's also look for how these functions are used in requests
import requests
import os

print("\n" + "="*50)
print("Directory structure around hooks.py:")
hooks_dir = os.path.dirname(requests.hooks.__file__)
for item in os.listdir(hooks_dir):
    if item.endswith('.py'):
        print(f"  {item}")