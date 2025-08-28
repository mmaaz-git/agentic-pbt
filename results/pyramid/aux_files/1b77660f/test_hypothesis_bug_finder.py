import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
from pyramid.location import inside, lineage


class SimpleObject:
    """Object that may or may not have __parent__"""
    def __init__(self, has_parent=True, parent_value=None):
        if has_parent:
            self.__parent__ = parent_value


@given(st.booleans(), st.booleans())
def test_inside_handles_missing_parent_attr(has_parent1, has_parent2):
    """Test that inside() handles objects without __parent__ attribute"""
    obj1 = SimpleObject(has_parent=has_parent1)
    obj2 = SimpleObject(has_parent=has_parent2)
    
    # This should not raise AttributeError
    result = inside(obj1, obj2)
    
    # If obj1 has no parent, it can only be inside obj2 if they're the same object
    if not has_parent1:
        assert result == (obj1 is obj2)


@given(st.booleans())
def test_lineage_vs_inside_consistency(has_parent):
    """Test that lineage() and inside() handle missing __parent__ consistently"""
    obj = SimpleObject(has_parent=has_parent)
    
    # lineage() handles missing __parent__ gracefully
    lineage_list = list(lineage(obj))
    assert len(lineage_list) >= 1
    assert lineage_list[0] is obj
    
    # inside() should also handle it
    # obj should be inside itself
    assert inside(obj, obj) == True


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])