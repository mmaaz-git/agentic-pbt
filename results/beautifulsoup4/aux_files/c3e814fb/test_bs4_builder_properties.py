"""Property-based tests for bs4.builder module"""

import bs4.builder
from bs4.builder import TreeBuilder, TreeBuilderRegistry, AttributeValueList
from hypothesis import given, strategies as st, assume, settings
import random
import string


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=10, alphabet=string.ascii_letters),  # builder name
            st.lists(st.text(min_size=1, max_size=10, alphabet=string.ascii_letters), min_size=1)  # features
        ),
        min_size=1,
        max_size=10
    ),
    st.lists(st.text(min_size=1, max_size=10, alphabet=string.ascii_letters), min_size=0, max_size=5)  # query features
)
def test_registry_lookup_feature_intersection(builders_with_features, query_features):
    """Test that lookup only returns builders with ALL requested features.
    
    According to the docstring: 'A TreeBuilder subclass, or None if there's no
    registered subclass with all the requested features.'
    """
    registry = TreeBuilderRegistry()
    
    # Create and register mock builders
    created_builders = []
    for i, (name, builder_features) in enumerate(builders_with_features):
        class MockBuilder(TreeBuilder):
            NAME = f"MockBuilder_{name}_{i}"
            features = builder_features
        created_builders.append(MockBuilder)
        registry.register(MockBuilder)
    
    # Perform lookup
    result = registry.lookup(*query_features)
    
    # Property: If a builder is returned, it must have ALL the requested features
    if result is not None:
        for feature in query_features:
            assert feature in result.features, f"Returned builder missing feature: {feature}"
    
    # Property: If no builder has all features, None should be returned
    if result is None:
        # Verify that indeed no builder has all the features
        has_all_features = False
        for builder in created_builders:
            if all(f in builder.features for f in query_features):
                has_all_features = True
                break
        assert not has_all_features, "Should have found a builder with all features"


@given(
    st.lists(
        st.tuples(
            st.text(min_size=1, max_size=10, alphabet=string.ascii_letters),  # builder name
            st.lists(st.text(min_size=1, max_size=10, alphabet=string.ascii_letters), min_size=1)  # features
        ),
        min_size=2,  # Need at least 2 to test priority
        max_size=10
    )
)
def test_registry_registration_order_priority(builders_with_features):
    """Test that most recently registered builders have priority.
    
    The code shows: self.builders.insert(0, treebuilder_class)
    This means the most recent registration should be first.
    """
    registry = TreeBuilderRegistry()
    
    # Create and register builders, tracking registration order
    created_builders = []
    shared_feature = "shared_feature_xyz"
    
    for i, (name, builder_features) in enumerate(builders_with_features):
        class MockBuilder(TreeBuilder):
            NAME = f"MockBuilder_{name}_{i}"
            registration_order = i
            features = builder_features + [shared_feature]  # Ensure all have at least one shared feature
        created_builders.append(MockBuilder)
        registry.register(MockBuilder)
    
    # Lookup with the shared feature
    result = registry.lookup(shared_feature)
    
    # Property: The most recently registered (highest index) should be returned
    if result is not None:
        expected_order = len(created_builders) - 1
        assert result.registration_order == expected_order, \
            f"Expected builder with order {expected_order}, got {result.registration_order}"


@given(
    st.text(min_size=1, max_size=20, alphabet=string.ascii_letters),  # tag name
    st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet=string.ascii_letters),  # attribute name
        st.text(min_size=0, max_size=30).map(lambda s: s.replace('\n', ' ').replace('\r', ' '))  # attribute value
    )
)
def test_replace_cdata_list_attribute_values_transformation(tag_name, attrs):
    """Test that _replace_cdata_list_attribute_values correctly splits whitespace-separated values.
    
    The docstring states: 'replaces class="foo bar" with class=["foo", "bar"]'
    """
    builder = TreeBuilder()
    
    # Configure which attributes should be treated as lists
    # Use 'class' and 'rel' as typical multi-valued attributes
    builder.cdata_list_attributes = {
        '*': {'class', 'rel'},
        tag_name.lower(): {'custom-attr'}
    }
    
    # Make a copy to compare
    original_attrs = dict(attrs)
    
    # Apply the transformation
    result = builder._replace_cdata_list_attribute_values(tag_name, attrs)
    
    # Property: Multi-valued attributes should be converted to lists
    for attr_name, attr_value in result.items():
        if attr_name in {'class', 'rel', 'custom-attr'}:
            if attr_name in original_attrs and original_attrs[attr_name]:
                # Should be converted to AttributeValueList with whitespace-split values
                assert isinstance(attr_value, AttributeValueList), \
                    f"Attribute {attr_name} should be AttributeValueList"
                
                # The list should contain the non-whitespace parts
                import re
                expected_parts = re.findall(r'\S+', original_attrs[attr_name])
                assert list(attr_value) == expected_parts, \
                    f"Expected {expected_parts}, got {list(attr_value)}"
        else:
            # Non-multi-valued attributes should remain unchanged
            if attr_name in original_attrs:
                assert attr_value == original_attrs[attr_name], \
                    f"Non-multi-valued attribute {attr_name} was modified"


@given(
    st.text(min_size=1, max_size=20, alphabet=string.ascii_letters),  # tag name
    st.one_of(
        st.none(),  # No empty_element_tags set
        st.sets(st.text(min_size=1, max_size=20, alphabet=string.ascii_letters))  # Set of tags
    )
)
def test_can_be_empty_element_logic(tag_name, empty_tags_set):
    """Test the can_be_empty_element method logic.
    
    According to the docstring and code:
    - If empty_element_tags is None, return True
    - Otherwise, return tag_name in empty_element_tags
    """
    builder = TreeBuilder()
    builder.empty_element_tags = empty_tags_set
    
    result = builder.can_be_empty_element(tag_name)
    
    # Property: Follows the documented logic
    if empty_tags_set is None:
        assert result is True, "Should return True when empty_element_tags is None"
    else:
        expected = tag_name in empty_tags_set
        assert result == expected, f"Expected {expected} for tag {tag_name}"


@given(st.integers(min_value=0, max_value=20))
def test_registry_lookup_no_features_returns_most_recent(num_builders):
    """Test that lookup with no features returns the most recently registered builder.
    
    The docstring states: 'If none are provided, the most recently registered 
    TreeBuilder subclass will be used.'
    """
    registry = TreeBuilderRegistry()
    
    if num_builders == 0:
        # No builders registered
        result = registry.lookup()
        assert result is None, "Should return None when no builders registered"
    else:
        # Register multiple builders
        last_builder = None
        for i in range(num_builders):
            class MockBuilder(TreeBuilder):
                NAME = f"MockBuilder_{i}"
                builder_id = i
                features = [f"feature_{i}"]
            registry.register(MockBuilder)
            last_builder = MockBuilder
        
        # Lookup with no features
        result = registry.lookup()
        
        # Should return the most recently registered
        assert result is not None, "Should return a builder"
        assert result.builder_id == num_builders - 1, \
            f"Should return most recent builder (id={num_builders-1}), got id={result.builder_id}"


if __name__ == "__main__":
    # Run a quick test
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])