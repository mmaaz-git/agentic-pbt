"""Minimal reproduction of TreeBuilderRegistry.lookup bug"""

from bs4.builder import TreeBuilder, TreeBuilderRegistry


# Create a simple test case
registry = TreeBuilderRegistry()

# Create a builder with only feature 'A'
class BuilderA(TreeBuilder):
    NAME = "BuilderA"
    features = ['A']

# Register it
registry.register(BuilderA)

# Try to lookup with features ['A', 'AA']
# According to the docstring, this should return None since no builder has ALL features
result = registry.lookup('A', 'AA')

print(f"Requested features: ['A', 'AA']")
print(f"Result: {result}")
if result:
    print(f"Result features: {result.features}")
    print(f"Has 'A': {'A' in result.features}")
    print(f"Has 'AA': {'AA' in result.features}")

# The bug: lookup returns BuilderA even though it doesn't have feature 'AA'
if result is not None:
    print("\n❌ BUG FOUND: lookup() returned a builder that doesn't have all requested features!")
    print(f"   Expected: None (no builder has both 'A' and 'AA')")
    print(f"   Got: {result} with features {result.features}")
else:
    print("\n✅ Correct: lookup() returned None as expected")