import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume
import pyramid.registry

# Test 1: Introspector add/get invariant
@given(
    category_name=st.text(min_size=1),
    discriminator=st.text(min_size=1),
    title=st.text(),
    type_name=st.text()
)
def test_introspector_add_get_invariant(category_name, discriminator, title, type_name):
    """Adding an introspectable and then getting it should return the same object"""
    introspector = pyramid.registry.Introspector()
    intr = pyramid.registry.Introspectable(category_name, discriminator, title, type_name)
    
    introspector.add(intr)
    retrieved = introspector.get(category_name, discriminator)
    
    assert retrieved is intr
    assert retrieved.category_name == category_name
    assert retrieved.discriminator == discriminator

# Test 2: Introspector remove makes item ungettable
@given(
    category_name=st.text(min_size=1),
    discriminator=st.text(min_size=1),
    title=st.text(),
    type_name=st.text()
)
def test_introspector_remove_makes_ungettable(category_name, discriminator, title, type_name):
    """After removing an introspectable, getting it should return None"""
    introspector = pyramid.registry.Introspector()
    intr = pyramid.registry.Introspectable(category_name, discriminator, title, type_name)
    
    introspector.add(intr)
    introspector.remove(category_name, discriminator)
    retrieved = introspector.get(category_name, discriminator)
    
    assert retrieved is None

# Test 3: Registry __bool__ always returns True
@given(
    data=st.dictionaries(st.text(), st.integers())
)
def test_registry_bool_always_true(data):
    """Registry should always evaluate to True, even when empty"""
    registry = pyramid.registry.Registry('test')
    
    # Empty registry should be True
    assert bool(registry) is True
    
    # Add data
    for k, v in data.items():
        registry[k] = v
    
    # Still should be True
    assert bool(registry) is True
    
    # Clear it
    registry.clear()
    
    # Still should be True
    assert bool(registry) is True

# Test 4: undefer is idempotent
@given(value=st.one_of(st.integers(), st.text(), st.none()))
def test_undefer_idempotent(value):
    """undefer should be idempotent - applying it multiple times gives same result"""
    # Test with non-Deferred values
    result1 = pyramid.registry.undefer(value)
    result2 = pyramid.registry.undefer(result1)
    assert result1 == result2 == value
    
    # Test with Deferred values
    deferred = pyramid.registry.Deferred(lambda: value)
    result1 = pyramid.registry.undefer(deferred)
    result2 = pyramid.registry.undefer(result1)
    assert result1 == result2 == value

# Test 5: Deferred.resolve() consistency
@given(value=st.one_of(st.integers(), st.text(), st.lists(st.integers())))
def test_deferred_resolve_consistency(value):
    """Deferred.resolve() should return the same value on multiple calls"""
    deferred = pyramid.registry.Deferred(lambda: value)
    
    result1 = deferred.resolve()
    result2 = deferred.resolve()
    result3 = deferred.value
    
    assert result1 == result2 == result3 == value

# Test 6: Introspectable discriminator_hash consistency
@given(
    category_name=st.text(min_size=1),
    discriminator=st.one_of(
        st.text(),
        st.tuples(st.text(), st.integers()),
        st.integers()
    ),
    title=st.text(),
    type_name=st.text()
)
def test_introspectable_discriminator_hash(category_name, discriminator, title, type_name):
    """discriminator_hash should be consistent with hash(discriminator)"""
    intr = pyramid.registry.Introspectable(category_name, discriminator, title, type_name)
    
    # The discriminator_hash should equal hash of the discriminator
    assert intr.discriminator_hash == hash(discriminator)
    
    # Calling it multiple times should give same result
    assert intr.discriminator_hash == intr.discriminator_hash

# Test 7: Introspector relate/unrelate inverse operations
@given(
    pairs=st.lists(
        st.tuples(
            st.text(min_size=1),  # category_name1
            st.text(min_size=1),  # discriminator1
            st.text(),             # title1
            st.text(),             # type_name1
            st.text(min_size=1),  # category_name2
            st.text(min_size=1),  # discriminator2
            st.text(),             # title2
            st.text()              # type_name2
        ),
        min_size=1,
        max_size=5
    )
)
def test_introspector_relate_unrelate_inverse(pairs):
    """relate followed by unrelate should restore original state"""
    introspector = pyramid.registry.Introspector()
    
    introspectables = []
    for cat1, disc1, title1, type1, cat2, disc2, title2, type2 in pairs:
        intr1 = pyramid.registry.Introspectable(cat1, disc1, title1, type1)
        intr2 = pyramid.registry.Introspectable(cat2, disc2, title2, type2)
        introspector.add(intr1)
        introspector.add(intr2)
        introspectables.append((intr1, intr2))
    
    # Check initial state - no relations
    for intr1, intr2 in introspectables:
        related = introspector.related(intr1)
        if intr1 != intr2:
            assert intr2 not in related
    
    # Relate all pairs
    for intr1, intr2 in introspectables:
        introspector.relate(
            (intr1.category_name, intr1.discriminator),
            (intr2.category_name, intr2.discriminator)
        )
    
    # Unrelate all pairs
    for intr1, intr2 in introspectables:
        introspector.unrelate(
            (intr1.category_name, intr1.discriminator),
            (intr2.category_name, intr2.discriminator)
        )
    
    # Check final state - should be back to no relations
    for intr1, intr2 in introspectables:
        related = introspector.related(intr1)
        if intr1 != intr2:
            assert intr2 not in related

# Test 8: Registry maintains dict interface
@given(
    items=st.dictionaries(
        st.text(min_size=1),
        st.one_of(st.integers(), st.text(), st.none()),
        max_size=10
    )
)
def test_registry_dict_interface(items):
    """Registry should maintain dict interface correctly"""
    registry = pyramid.registry.Registry('test')
    
    # Test setting items
    for k, v in items.items():
        registry[k] = v
    
    # Test getting items
    for k, v in items.items():
        assert registry[k] == v
        assert registry.get(k) == v
    
    # Test keys, values, items
    assert set(registry.keys()) == set(items.keys())
    assert set(registry.values()) == set(items.values())
    assert set(registry.items()) == set(items.items())
    
    # Test len
    assert len(registry) == len(items)
    
    # Test contains
    for k in items:
        assert k in registry

# Test 9: Introspector get_category returns sorted introspectables
@given(
    introspectables=st.lists(
        st.tuples(
            st.text(min_size=1),  # discriminator
            st.text(),             # title
            st.text()              # type_name
        ),
        min_size=1,
        max_size=10
    )
)
def test_introspector_get_category_sorted(introspectables):
    """get_category should return introspectables sorted by order"""
    introspector = pyramid.registry.Introspector()
    category_name = "test_category"
    
    intrs = []
    for disc, title, type_name in introspectables:
        intr = pyramid.registry.Introspectable(category_name, disc, title, type_name)
        introspector.add(intr)
        intrs.append(intr)
    
    # Get the category
    result = introspector.get_category(category_name)
    
    # Check that results are sorted by order
    if result:
        orders = [item['introspectable'].order for item in result]
        assert orders == sorted(orders)
        
        # Check all introspectables are present
        result_intrs = [item['introspectable'] for item in result]
        assert set(result_intrs) == set(intrs)