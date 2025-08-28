import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pyramid.registry
import threading
import time

# Test 10: Introspector handles discriminator hash collisions
@given(
    data=st.data(),
    category_name=st.text(min_size=1)
)
def test_introspector_discriminator_hash_access(data, category_name):
    """Test that introspector can handle both discriminator and discriminator_hash access"""
    introspector = pyramid.registry.Introspector()
    
    # Create introspectables
    discriminators = data.draw(st.lists(st.text(min_size=1), min_size=2, max_size=5, unique=True))
    
    intrs = []
    for disc in discriminators:
        intr = pyramid.registry.Introspectable(category_name, disc, "title", "type")
        introspector.add(intr)
        intrs.append(intr)
    
    # Should be able to get by discriminator
    for intr in intrs:
        retrieved = introspector.get(category_name, intr.discriminator)
        assert retrieved is intr
        
        # Should also be able to get by discriminator_hash
        retrieved_by_hash = introspector.get(category_name, intr.discriminator_hash)
        assert retrieved_by_hash is intr

# Test 11: Complex relate scenarios with self-relations
@given(
    category_name=st.text(min_size=1),
    discriminator=st.text(min_size=1)
)
def test_introspector_self_relation(category_name, discriminator):
    """Test that self-relations are handled correctly"""
    introspector = pyramid.registry.Introspector()
    
    intr = pyramid.registry.Introspectable(category_name, discriminator, "title", "type")
    introspector.add(intr)
    
    # Relate to itself
    introspector.relate(
        (category_name, discriminator),
        (category_name, discriminator)
    )
    
    # Self should not appear in related list (based on code: if x is not y)
    related = introspector.related(intr)
    assert intr not in related

# Test 12: Deferred with exceptions
@given(
    error_msg=st.text()
)
def test_deferred_with_exception(error_msg):
    """Test that Deferred properly propagates exceptions"""
    def failing_func():
        raise ValueError(error_msg)
    
    deferred = pyramid.registry.Deferred(failing_func)
    
    # First call should raise
    try:
        result1 = deferred.resolve()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert str(e) == error_msg
    
    # Second call should raise the same (cached) exception
    try:
        result2 = deferred.value
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert str(e) == error_msg

# Test 13: Registry settings property
@given(
    settings_dict=st.dictionaries(st.text(min_size=1), st.integers())
)
def test_registry_settings_property(settings_dict):
    """Test Registry settings property registration"""
    registry = pyramid.registry.Registry('test')
    
    # Set settings
    registry.settings = settings_dict
    
    # Should be retrievable via property
    assert registry.settings == settings_dict
    
    # Should also be registered as utility (based on code)
    from pyramid.interfaces import ISettings
    retrieved_settings = registry.getUtility(ISettings)
    assert retrieved_settings == settings_dict

# Test 14: Introspectable's unrelate before relate
@given(
    cat1=st.text(min_size=1),
    disc1=st.text(min_size=1),
    cat2=st.text(min_size=1),
    disc2=st.text(min_size=1)
)
def test_introspectable_unrelate_before_relate(cat1, disc1, cat2, disc2):
    """Test that unrelate before relate doesn't cause issues"""
    assume((cat1, disc1) != (cat2, disc2))
    
    intr1 = pyramid.registry.Introspectable(cat1, disc1, "t1", "type1")
    intr2 = pyramid.registry.Introspectable(cat2, disc2, "t2", "type2")
    
    # Unrelate before they're related
    intr1.unrelate(cat2, disc2)
    intr2.unrelate(cat1, disc1)
    
    introspector = pyramid.registry.Introspector()
    
    # Register them (this processes the unrelate commands)
    intr1.register(introspector, None)
    intr2.register(introspector, None)
    
    # They should not be related
    related1 = introspector.related(intr1)
    related2 = introspector.related(intr2)
    
    assert intr2 not in related1
    assert intr1 not in related2

# Test 15: predvalseq is a proper tuple subclass
@given(
    values=st.lists(st.integers())
)
def test_predvalseq_tuple_behavior(values):
    """predvalseq should behave as a tuple"""
    pv = pyramid.registry.predvalseq(values)
    
    # Should be a tuple
    assert isinstance(pv, tuple)
    
    # Should have same values
    assert list(pv) == values
    
    # Should support tuple operations
    if values:
        assert pv[0] == values[0]
        assert len(pv) == len(values)
        assert pv.count(values[0]) == values.count(values[0])

# Test 16: Registry view cache thread safety (basic check)
@given(
    keys=st.lists(st.text(min_size=1), min_size=5, max_size=10, unique=True)
)
@settings(deadline=1000)
def test_registry_view_cache_concurrent_clear(keys):
    """Test that concurrent cache clears don't cause issues"""
    registry = pyramid.registry.Registry('test')
    
    # Add some items to the view cache
    for key in keys:
        registry._view_lookup_cache[key] = f"value_{key}"
    
    def clear_cache():
        registry._clear_view_lookup_cache()
    
    # Run concurrent clears
    threads = []
    for _ in range(5):
        t = threading.Thread(target=clear_cache)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Cache should be empty
    assert registry._view_lookup_cache == {}

# Test 17: Introspector categories() returns sorted list
@given(
    category_names=st.lists(st.text(min_size=1), min_size=1, max_size=10, unique=True)
)
def test_introspector_categories_sorted(category_names):
    """categories() should return sorted category names"""
    introspector = pyramid.registry.Introspector()
    
    for cat_name in category_names:
        intr = pyramid.registry.Introspectable(cat_name, "disc", "title", "type")
        introspector.add(intr)
    
    categories = introspector.categories()
    
    # Should be sorted
    assert categories == sorted(category_names)
    
    # Should contain all categories
    assert set(categories) == set(category_names)

# Test 18: Registry package_name property
@given(
    package_name=st.one_of(
        st.text(min_size=1),
        st.just(None)
    )
)
def test_registry_package_name(package_name):
    """Registry package_name should be accessible via property"""
    if package_name is None:
        # When None or CALLER_PACKAGE, it uses caller_package()
        registry = pyramid.registry.Registry()
        # package_name should be set to something (the caller module name)
        assert registry.package_name is not None
        assert isinstance(registry.package_name, str)
    else:
        registry = pyramid.registry.Registry(package_name)
        assert registry.package_name == package_name

# Test 19: Introspectable as dict
@given(
    cat_name=st.text(min_size=1),
    disc=st.text(min_size=1),
    dict_items=st.dictionaries(st.text(), st.integers(), max_size=5)
)
def test_introspectable_dict_interface(cat_name, disc, dict_items):
    """Introspectable inherits from dict and should support dict operations"""
    intr = pyramid.registry.Introspectable(cat_name, disc, "title", "type")
    
    # Should support dict operations
    for k, v in dict_items.items():
        intr[k] = v
    
    for k, v in dict_items.items():
        assert intr[k] == v
        assert intr.get(k) == v
    
    assert set(intr.keys()) >= set(dict_items.keys())
    
    # __bool__ should always return True
    assert bool(intr) is True
    
    # Clear and check
    intr.clear()
    assert bool(intr) is True  # Still True even when empty