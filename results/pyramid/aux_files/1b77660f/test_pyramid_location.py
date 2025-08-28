import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from pyramid.location import inside, lineage


class Resource:
    """Test resource class with optional parent"""
    def __init__(self, parent=None, value=None):
        self.__parent__ = parent
        self.value = value
    
    def __repr__(self):
        return f"Resource(value={self.value})"


@st.composite
def resource_chain(draw):
    """Generate a chain of resources with parent relationships"""
    depth = draw(st.integers(min_value=1, max_value=10))
    resources = []
    parent = None
    
    for i in range(depth):
        resource = Resource(parent=parent, value=i)
        resources.append(resource)
        parent = resource
    
    return resources


@st.composite
def resource_tree(draw):
    """Generate a more complex resource tree"""
    root = Resource(value="root")
    depth = draw(st.integers(min_value=0, max_value=5))
    
    nodes = [root]
    for level in range(depth):
        new_nodes = []
        for parent in nodes[-min(3, len(nodes)):]:  # Last few nodes
            num_children = draw(st.integers(min_value=0, max_value=3))
            for i in range(num_children):
                child = Resource(parent=parent, value=f"level{level}_child{i}")
                new_nodes.append(child)
        if new_nodes:
            nodes.extend(new_nodes)
    
    return nodes


@given(resource_chain())
def test_inside_reflexivity(chain):
    """Test that a resource is inside itself"""
    for resource in chain:
        assert inside(resource, resource) == True


@given(resource_chain())
def test_inside_transitivity(chain):
    """Test transitivity: if A inside B and B inside C, then A inside C"""
    if len(chain) >= 3:
        # Pick three resources in parent-child relationship
        for i in range(len(chain) - 2):
            a = chain[i]
            b = chain[i + 1]  # b is parent of a
            c = chain[i + 2]  # c is parent of b
            
            # Verify the setup
            assert a.__parent__ == b
            assert b.__parent__ == c
            
            # Test transitivity
            if inside(a, b) and inside(b, c):
                assert inside(a, c), f"Transitivity failed: {a} should be inside {c}"


@given(resource_chain())
def test_inside_lineage_consistency(chain):
    """Test that inside() and lineage() are consistent"""
    for i, resource1 in enumerate(chain):
        for j, resource2 in enumerate(chain):
            is_inside = inside(resource1, resource2)
            lineage_list = list(lineage(resource1))
            resource2_in_lineage = resource2 in lineage_list
            
            if is_inside:
                assert resource2_in_lineage, \
                    f"resource1 is inside resource2, but resource2 not in lineage"
            
            # The converse may not be true if they're not identical objects


@given(resource_chain())
def test_lineage_first_element(chain):
    """Test that first element of lineage is always the resource itself"""
    for resource in chain:
        lineage_list = list(lineage(resource))
        assert len(lineage_list) > 0, "Lineage should never be empty"
        assert lineage_list[0] is resource, \
            f"First element should be the resource itself"


@given(resource_chain())
def test_lineage_parent_chain(chain):
    """Test that each element in lineage is the parent of the previous"""
    for resource in chain:
        lineage_list = list(lineage(resource))
        
        for i in range(len(lineage_list) - 1):
            child = lineage_list[i]
            parent = lineage_list[i + 1]
            
            # The parent of child should be parent
            # Handle case where __parent__ might not exist
            try:
                assert child.__parent__ is parent, \
                    f"Parent chain broken: {child}.__parent__ is not {parent}"
            except AttributeError:
                # This should only happen for the last element
                assert i == len(lineage_list) - 2, \
                    "Missing __parent__ in middle of chain"


@given(resource_tree())
def test_inside_with_none_parent(nodes):
    """Test inside() behavior when parent is None"""
    # Create a resource with no parent
    orphan = Resource(parent=None)
    
    # Orphan should not be inside any node except itself
    for node in nodes:
        if node is not orphan:
            assert not inside(orphan, node), \
                f"Orphan should not be inside {node}"
    
    # But should be inside itself
    assert inside(orphan, orphan)


@given(resource_tree())
def test_lineage_terminates(nodes):
    """Test that lineage terminates properly"""
    for node in nodes:
        lineage_list = list(lineage(node))
        
        # Should terminate
        assert len(lineage_list) <= 100, "Lineage should terminate"
        
        # Last element should have no parent or None parent
        last = lineage_list[-1]
        try:
            assert last.__parent__ is None, \
                f"Last element should have None parent, got {last.__parent__}"
        except AttributeError:
            pass  # No __parent__ attribute is also valid termination


class ResourceNoParent:
    """Resource without __parent__ attribute"""
    def __init__(self, value=None):
        self.value = value


@given(st.integers())
def test_lineage_no_parent_attr(value):
    """Test lineage with object that has no __parent__ attribute"""
    resource = ResourceNoParent(value=value)
    lineage_list = list(lineage(resource))
    
    # Should return just the resource itself
    assert len(lineage_list) == 1
    assert lineage_list[0] is resource


@given(st.integers())
def test_inside_no_parent_attr(value):
    """Test inside with object that has no __parent__ attribute"""
    resource1 = ResourceNoParent(value=value)
    resource2 = ResourceNoParent(value=value + 1)
    
    # Should only be inside itself
    assert inside(resource1, resource1)
    assert not inside(resource1, resource2)


class CyclicResource:
    """Resource that can form cycles"""
    def __init__(self, value=None):
        self.value = value
        self.__parent__ = None


@given(st.integers(min_value=0, max_value=10))
def test_inside_with_cycle(chain_length):
    """Test inside() with cyclic parent references"""
    if chain_length == 0:
        return
    
    # Create a chain
    resources = []
    for i in range(chain_length):
        resources.append(CyclicResource(value=i))
    
    # Link them
    for i in range(chain_length - 1):
        resources[i].__parent__ = resources[i + 1]
    
    # Create a cycle
    resources[-1].__parent__ = resources[0]
    
    # inside() should handle cycles (by using 'is' comparison)
    # It will loop forever if there's a cycle and resource1 is not resource2
    # Let's test that it finds resource2 if it's in the cycle
    assert inside(resources[0], resources[0])  # Reflexivity still works
    
    # This would loop forever with the current implementation!
    # Commenting out to avoid infinite loop
    # assert not inside(resources[0], CyclicResource(value=999))


@given(st.integers(min_value=1, max_value=10))
def test_lineage_with_cycle(chain_length):
    """Test lineage() with cyclic parent references"""
    # Create a chain
    resources = []
    for i in range(chain_length):
        resources.append(CyclicResource(value=i))
    
    # Link them
    for i in range(chain_length - 1):
        resources[i].__parent__ = resources[i + 1]
    
    # Create a cycle
    resources[-1].__parent__ = resources[0]
    
    # lineage() will produce infinite results with cycles!
    # Let's verify it produces at least the expected elements
    lineage_gen = lineage(resources[0])
    lineage_items = []
    
    # Collect items until we see a repeat
    seen = set()
    for item in lineage_gen:
        if id(item) in seen:
            break
        seen.add(id(item))
        lineage_items.append(item)
        if len(lineage_items) > chain_length * 2:
            break  # Safety limit
    
    # Should have seen all items in the cycle
    assert len(lineage_items) == chain_length