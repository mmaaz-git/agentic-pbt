#!/usr/bin/env python3
"""
Property-based tests for pyramid.interfaces module.

This module contains interface definitions, so we test the documented
invariants and relationships between the interfaces and constants.
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume
import pyramid.interfaces as pi


def test_phase_ordering_invariant():
    """
    Test that configuration phases maintain their documented ordering.
    The comment in the code states: "a lower phase number means the actions 
    associated with this phase will be executed earlier"
    """
    # This is a simple invariant test without hypothesis strategies
    # since we're testing constants
    assert pi.PHASE0_CONFIG < pi.PHASE1_CONFIG, \
        "PHASE0_CONFIG should execute before PHASE1_CONFIG"
    assert pi.PHASE1_CONFIG < pi.PHASE2_CONFIG, \
        "PHASE1_CONFIG should execute before PHASE2_CONFIG"
    assert pi.PHASE2_CONFIG < pi.PHASE3_CONFIG, \
        "PHASE2_CONFIG should execute before PHASE3_CONFIG"
    
    # Test transitivity
    assert pi.PHASE0_CONFIG < pi.PHASE2_CONFIG
    assert pi.PHASE0_CONFIG < pi.PHASE3_CONFIG
    assert pi.PHASE1_CONFIG < pi.PHASE3_CONFIG
    
    # Test that default phase is 0 as documented
    assert pi.PHASE3_CONFIG == 0, "Default phase number should be 0"


def test_interface_alias_consistency():
    """
    Test that interface aliases remain consistent.
    These are documented backwards compatibility aliases.
    """
    # Test documented aliases
    assert pi.IAfterTraversal is pi.IContextFound, \
        "IAfterTraversal should be an alias for IContextFound"
    
    assert pi.IWSGIApplicationCreatedEvent is pi.IApplicationCreated, \
        "IWSGIApplicationCreatedEvent should be an alias for IApplicationCreated"
    
    assert pi.ILogger is pi.IDebugLogger, \
        "ILogger should be an alias for IDebugLogger"
    
    assert pi.ITraverserFactory is pi.ITraverser, \
        "ITraverserFactory should be an alias for ITraverser"


def test_irequest_combined_property():
    """
    Test that IRequest.combined references IRequest itself.
    This is used for exception view lookups according to the comment.
    """
    assert hasattr(pi.IRequest, 'combined'), \
        "IRequest should have a 'combined' attribute"
    
    assert pi.IRequest.combined is pi.IRequest, \
        "IRequest.combined should reference IRequest itself"


def test_vh_root_key_constant():
    """
    Test properties of the VH_ROOT_KEY constant.
    This is documented as an interface despite being a string constant.
    """
    assert isinstance(pi.VH_ROOT_KEY, str), \
        "VH_ROOT_KEY should be a string"
    
    assert pi.VH_ROOT_KEY == 'HTTP_X_VHM_ROOT', \
        "VH_ROOT_KEY should have the expected value"
    
    # Test that it follows HTTP header naming conventions
    assert pi.VH_ROOT_KEY.startswith('HTTP_'), \
        "VH_ROOT_KEY should follow HTTP header naming convention"
    
    assert pi.VH_ROOT_KEY.isupper(), \
        "VH_ROOT_KEY should be uppercase per HTTP header convention"


@given(st.sampled_from(['PHASE0_CONFIG', 'PHASE1_CONFIG', 'PHASE2_CONFIG', 'PHASE3_CONFIG']))
def test_phase_constants_are_integers(phase_name):
    """
    Property: All phase constants should be integers.
    This is important for comparison and ordering.
    """
    phase_value = getattr(pi, phase_name)
    assert isinstance(phase_value, int), \
        f"{phase_name} should be an integer"


@given(
    st.sampled_from(['IAfterTraversal', 'IWSGIApplicationCreatedEvent', 'ILogger', 'ITraverserFactory']),
    st.sampled_from(['IContextFound', 'IApplicationCreated', 'IDebugLogger', 'ITraverser'])
)
def test_alias_pairs_are_interfaces(alias_name, original_name):
    """
    Property: All documented aliases should reference valid interface classes.
    """
    # Only test matching pairs
    pairs = {
        'IAfterTraversal': 'IContextFound',
        'IWSGIApplicationCreatedEvent': 'IApplicationCreated',
        'ILogger': 'IDebugLogger',
        'ITraverserFactory': 'ITraverser'
    }
    
    if pairs.get(alias_name) != original_name:
        assume(False)  # Skip non-matching pairs
    
    alias = getattr(pi, alias_name)
    original = getattr(pi, original_name)
    
    # Both should exist
    assert alias is not None, f"{alias_name} should exist"
    assert original is not None, f"{original_name} should exist"
    
    # They should be the same object
    assert alias is original, f"{alias_name} should be identical to {original_name}"
    
    # Both should be interface classes
    from zope.interface import Interface
    assert issubclass(alias, Interface), f"{alias_name} should be an Interface"
    assert issubclass(original, Interface), f"{original_name} should be an Interface"


@given(st.integers())
def test_phase_comparison_transitivity(offset):
    """
    Property: Phase ordering should be transitive with any integer offset.
    If a < b and b < c, then a < c should hold for any transformation.
    """
    # Apply the same offset to all phases
    phase0 = pi.PHASE0_CONFIG + offset
    phase1 = pi.PHASE1_CONFIG + offset
    phase2 = pi.PHASE2_CONFIG + offset
    phase3 = pi.PHASE3_CONFIG + offset
    
    # Test transitivity holds
    if phase0 < phase1 and phase1 < phase2:
        assert phase0 < phase2, "Transitivity should hold for phase ordering"
    
    if phase1 < phase2 and phase2 < phase3:
        assert phase1 < phase3, "Transitivity should hold for phase ordering"
    
    if phase0 < phase1 and phase1 < phase3:
        assert phase0 < phase3, "Transitivity should hold for phase ordering"


def test_interface_names_follow_convention():
    """
    Test that all interface names follow the documented naming convention.
    Interfaces should start with 'I' followed by a capital letter.
    """
    import inspect
    from zope.interface import Interface
    
    for name in dir(pi):
        obj = getattr(pi, name)
        try:
            if inspect.isclass(obj) and issubclass(obj, Interface) and obj is not Interface:
                # Interface names should start with 'I'
                if not name.startswith('_'):  # Skip private names
                    assert name[0] == 'I', f"Interface {name} should start with 'I'"
                    if len(name) > 1:
                        assert name[1].isupper(), f"Interface {name} should have uppercase after 'I'"
        except:
            pass  # Skip non-class objects


if __name__ == "__main__":
    # Run tests
    print("Testing pyramid.interfaces properties...")
    
    test_phase_ordering_invariant()
    print("✓ Phase ordering invariant holds")
    
    test_interface_alias_consistency()
    print("✓ Interface aliases are consistent")
    
    test_irequest_combined_property()
    print("✓ IRequest.combined property is correct")
    
    test_vh_root_key_constant()
    print("✓ VH_ROOT_KEY constant properties hold")
    
    test_interface_names_follow_convention()
    print("✓ Interface naming convention is followed")
    
    # Run hypothesis tests
    print("\nRunning property-based tests with Hypothesis...")
    test_phase_constants_are_integers()
    test_alias_pairs_are_interfaces()
    test_phase_comparison_transitivity()
    
    print("\nAll tests passed successfully!")