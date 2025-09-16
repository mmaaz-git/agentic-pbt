import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

from coremltools.converters.mil.input_types import EnumeratedShapes

print("Checking EnumeratedShapes.__init__ documentation:")
print("="*60)
print(EnumeratedShapes.__init__.__doc__)
print("="*60)