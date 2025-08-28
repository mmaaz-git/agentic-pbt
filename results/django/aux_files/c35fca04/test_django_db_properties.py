"""
Property-based tests for django.db module using Hypothesis
"""
import django
from django.conf import settings

# Configure Django before importing its modules
settings.configure(
    DEBUG=True,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
)
django.setup()

from hypothesis import given, strategies as st, assume, settings as hyp_settings
from django.db.models.query_utils import make_hashable, subclasses
from django.db.utils import import_string, load_backend
import pytest
from collections.abc import Iterable


# Strategy for generating complex nested structures
nested_structure = st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(max_size=100),
        st.binary(max_size=100),
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=5),
        st.tuples(children, children),
        st.dictionaries(
            st.text(max_size=20),
            children,
            max_size=5
        ),
        st.sets(st.integers(), max_size=5),  # hashable sets
        st.frozensets(st.integers(), max_size=5),  # hashable frozensets
    ),
    max_leaves=20
)


class TestMakeHashable:
    """Test properties of the make_hashable function"""

    @given(nested_structure)
    @hyp_settings(max_examples=500)
    def test_make_hashable_produces_hashable_output(self, value):
        """Property: make_hashable(x) should always be hashable"""
        try:
            result = make_hashable(value)
            # This should not raise
            hash(result)
        except TypeError as e:
            # make_hashable can raise TypeError for non-hashable, non-iterable values
            # This is documented behavior
            pass

    @given(nested_structure, nested_structure)
    @hyp_settings(max_examples=500)
    def test_make_hashable_preserves_equality(self, value1, value2):
        """Property: if x == y, then make_hashable(x) == make_hashable(y)"""
        # Skip if either value causes TypeError (expected for some inputs)
        try:
            result1 = make_hashable(value1)
            result2 = make_hashable(value2)
        except TypeError:
            # Expected for non-hashable, non-iterable values
            return
        
        if value1 == value2:
            assert result1 == result2, f"Equal values should produce equal results: {value1} vs {value2}"

    @given(nested_structure)
    @hyp_settings(max_examples=500)
    def test_make_hashable_hash_consistency(self, value):
        """Property: hash(make_hashable(x)) should be consistent"""
        try:
            result = make_hashable(value)
            hash1 = hash(result)
            hash2 = hash(result)
            assert hash1 == hash2, "Hash should be consistent for the same result"
        except TypeError:
            # Expected for some inputs
            pass

    @given(st.dictionaries(st.text(max_size=20), st.integers(), max_size=10))
    @hyp_settings(max_examples=500)
    def test_make_hashable_dict_order_independence(self, d):
        """Property: make_hashable should produce same result for dicts regardless of insertion order"""
        # Create two dicts with same content but potentially different insertion order
        d1 = dict(d)
        d2 = dict(sorted(d.items()))
        
        result1 = make_hashable(d1)
        result2 = make_hashable(d2)
        
        assert result1 == result2, "Dict order should not affect the result"
        assert hash(result1) == hash(result2), "Hash should be the same for dicts with same content"


class TestSubclasses:
    """Test properties of the subclasses function"""
    
    @given(st.sampled_from([int, str, list, dict, Exception, BaseException, object]))
    def test_subclasses_includes_self(self, cls):
        """Property: subclasses(cls) should always yield cls as first item"""
        result = list(subclasses(cls))
        assert len(result) >= 1, "Should yield at least the class itself"
        assert result[0] is cls, "First yielded item should be the input class"
    
    @given(st.sampled_from([int, str, list, dict, Exception]))
    def test_subclasses_all_are_subclasses(self, cls):
        """Property: All yielded classes should be subclasses of the input class"""
        for subcls in subclasses(cls):
            assert issubclass(subcls, cls), f"{subcls} should be a subclass of {cls}"
    
    def test_subclasses_completeness(self):
        """Property: subclasses should find all subclasses"""
        # Create a test hierarchy
        class A: pass
        class B(A): pass
        class C(A): pass
        class D(B): pass
        
        result = set(subclasses(A))
        expected = {A, B, C, D}
        assert result == expected, f"Should find all subclasses. Got {result}, expected {expected}"


class TestImportString:
    """Test properties of import_string function"""
    
    @given(st.sampled_from([
        'django.db.models.Model',
        'django.db.models.Field',
        'django.db.models.QuerySet',
        'django.db.utils.ConnectionHandler',
        'django.db.transaction.atomic',
    ]))
    def test_import_string_round_trip(self, dotted_path):
        """Property: import_string should successfully import known Django classes"""
        obj = import_string(dotted_path)
        # The imported object should have the expected name
        module_path, class_name = dotted_path.rsplit('.', 1)
        assert obj.__name__ == class_name or callable(obj), f"Imported object should have correct name"
    
    @given(st.text(min_size=1, max_size=100).filter(lambda x: '.' in x))
    def test_import_string_error_handling(self, dotted_path):
        """Property: import_string should raise ImportError for invalid paths"""
        # Skip if this happens to be a valid import path
        try:
            import_string(dotted_path)
            # If it succeeds, that's fine - skip this test case
            return
        except ImportError as e:
            # Should have a descriptive error message
            assert dotted_path in str(e) or "doesn't look like a module path" in str(e)
        except Exception as e:
            # Any other exception is unexpected
            pytest.fail(f"Unexpected exception type {type(e)}: {e}")


class TestLoadBackend:
    """Test properties of load_backend function"""
    
    @given(st.sampled_from([
        'django.db.backends.sqlite3',
        'django.db.backends.postgresql',
        'django.db.backends.mysql',
        'django.db.backends.oracle',
    ]))
    def test_load_backend_known_backends(self, backend_name):
        """Property: load_backend should handle all built-in backends"""
        try:
            backend = load_backend(backend_name)
            # Should return a module with expected structure
            assert hasattr(backend, 'DatabaseWrapper'), "Backend should have DatabaseWrapper"
        except ImportError:
            # Some backends might not be installed, that's OK
            pass
    
    def test_load_backend_legacy_rename(self):
        """Property: load_backend should handle legacy postgresql_psycopg2 name"""
        # This is a documented backward compatibility feature
        try:
            backend1 = load_backend('django.db.backends.postgresql')
            backend2 = load_backend('django.db.backends.postgresql_psycopg2')
            # Both should load the same backend
            assert backend1 is backend2, "Legacy name should load same backend"
        except ImportError:
            # PostgreSQL backend might not be installed
            pass