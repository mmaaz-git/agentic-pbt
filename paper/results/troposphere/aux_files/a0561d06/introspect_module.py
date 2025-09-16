import sys
import inspect
import os

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.codeguruprofiler as cgp

print("Module file:", cgp.__file__)
print("\nModule directory:", os.path.dirname(cgp.__file__))
print("\nPublic members of troposphere.codeguruprofiler:")

members = inspect.getmembers(cgp)
for name, obj in members:
    if not name.startswith('_'):
        obj_type = type(obj).__name__
        print(f"  {name}: {obj_type}")
        if inspect.isclass(obj):
            # Show class methods
            class_members = [m for m, _ in inspect.getmembers(obj) if not m.startswith('_')]
            if class_members:
                print(f"    Members: {', '.join(class_members[:10])}")  # First 10 members