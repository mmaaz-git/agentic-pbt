"""Demonstrate the TreeBuilderRegistry.lookup bug with multiple test cases"""

from bs4.builder import TreeBuilder, TreeBuilderRegistry


def test_case_1():
    """Test case 1: Request features ['A', 'NonExistent']"""
    registry = TreeBuilderRegistry()
    
    class BuilderA(TreeBuilder):
        features = ['A', 'B']
    
    registry.register(BuilderA)
    
    # Should return None since no builder has 'NonExistent'
    result = registry.lookup('A', 'NonExistent')
    
    print("Test 1: Request ['A', 'NonExistent'] when only BuilderA with ['A', 'B'] exists")
    print(f"  Result: {result}")
    print(f"  Expected: None")
    print(f"  Status: {'❌ FAIL' if result else '✅ PASS'}")
    return result is None


def test_case_2():
    """Test case 2: Request features where first exists, second doesn't"""
    registry = TreeBuilderRegistry()
    
    class Builder1(TreeBuilder):
        features = ['xml', 'fast']
    
    class Builder2(TreeBuilder):
        features = ['html', 'fast']
    
    registry.register(Builder1)
    registry.register(Builder2)
    
    # Should return None since no builder has 'nonexistent'
    result = registry.lookup('fast', 'nonexistent')
    
    print("\nTest 2: Request ['fast', 'nonexistent'] with multiple builders")
    print(f"  Builder1: ['xml', 'fast']")
    print(f"  Builder2: ['html', 'fast']")
    print(f"  Result: {result}")
    print(f"  Expected: None")
    print(f"  Status: {'❌ FAIL' if result else '✅ PASS'}")
    return result is None


def test_case_3():
    """Test case 3: Request features in different order"""
    registry = TreeBuilderRegistry()
    
    class BuilderX(TreeBuilder):
        features = ['feature1']
    
    registry.register(BuilderX)
    
    # Both should return None
    result1 = registry.lookup('feature1', 'feature2')
    result2 = registry.lookup('feature2', 'feature1')
    
    print("\nTest 3: Feature order shouldn't matter")
    print(f"  BuilderX has: ['feature1']")
    print(f"  lookup('feature1', 'feature2'): {result1}")
    print(f"  lookup('feature2', 'feature1'): {result2}")
    print(f"  Both should be None")
    print(f"  Status: {'✅ PASS' if not result1 and not result2 else '❌ FAIL'}")
    return result1 is None and result2 is None


def test_case_4():
    """Test case 4: Correct behavior when all features exist"""
    registry = TreeBuilderRegistry()
    
    class GoodBuilder(TreeBuilder):
        features = ['A', 'B', 'C']
    
    registry.register(GoodBuilder)
    
    # Should return GoodBuilder since it has all features
    result = registry.lookup('A', 'B')
    
    print("\nTest 4: Request ['A', 'B'] when builder has ['A', 'B', 'C']")
    print(f"  Result: {result}")
    print(f"  Expected: GoodBuilder")
    print(f"  Status: {'✅ PASS' if result == GoodBuilder else '❌ FAIL'}")
    return result == GoodBuilder


# Run all tests
print("Testing TreeBuilderRegistry.lookup() behavior")
print("=" * 50)

results = [
    test_case_1(),
    test_case_2(),
    test_case_3(),
    test_case_4()
]

print("\n" + "=" * 50)
print(f"Summary: {sum(results)}/{len(results)} tests passed")

if not all(results):
    print("\n🐛 BUG CONFIRMED: TreeBuilderRegistry.lookup() returns builders")
    print("   that don't have all requested features when some features")
    print("   are not present in any registered builder.")