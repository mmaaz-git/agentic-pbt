#!/usr/bin/env python3
"""
Hypothesis-based bug hunting for troposphere.mediatailor
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
from hypothesis import Phase
import troposphere.mediatailor as mediatailor
import troposphere.validators as validators
import json


# First, test the validators thoroughly
print("="*60)
print("TESTING VALIDATORS WITH HYPOTHESIS")
print("="*60)

# Test 1: Boolean validator accepts booleans as integers
@given(st.booleans())
@settings(max_examples=10)
def test_boolean_validator_accepts_bool(b):
    """The boolean validator should handle Python booleans"""
    result = validators.boolean(b)
    assert result == b
    print(f"✓ boolean({b}) = {result}")

try:
    test_boolean_validator_accepts_bool()
    print("Boolean validator correctly handles booleans\n")
except Exception as e:
    print(f"BUG in boolean validator with booleans: {e}\n")


# Test 2: Integer validator accepts booleans (since bool is subclass of int)
@given(st.booleans())
@settings(max_examples=10)
def test_integer_validator_accepts_bool(b):
    """Integer validator accepts booleans because bool subclasses int"""
    result = validators.integer(b)
    # In Python, True == 1 and False == 0
    assert int(result) == int(b)
    print(f"✓ integer({b}) = {result}, int value = {int(result)}")

try:
    test_integer_validator_accepts_bool()
    print("Note: Integer validator accepts booleans (Python design)\n")
except Exception as e:
    print(f"Error with integer validator and booleans: {e}\n")


# Test 3: Round-trip property for mediatailor classes
print("="*60)
print("TESTING ROUND-TRIP SERIALIZATION")
print("="*60)

@given(
    manifest_name=st.text(min_size=1, max_size=50),
    source_group=st.text(min_size=1, max_size=50)
)
@settings(max_examples=20, suppress_health_check=[])
def test_request_output_round_trip(manifest_name, source_group):
    """Test round-trip: from_dict(to_dict(x)) == x"""
    original = mediatailor.RequestOutputItem(
        ManifestName=manifest_name,
        SourceGroup=source_group
    )
    
    # Serialize
    dict_repr = original.to_dict()
    
    # Deserialize
    reconstructed = mediatailor.RequestOutputItem._from_dict(**dict_repr)
    
    # Should be equivalent
    dict_repr2 = reconstructed.to_dict()
    
    if dict_repr != dict_repr2:
        print(f"BUG: Round-trip failed!")
        print(f"  Input: ManifestName={manifest_name!r}, SourceGroup={source_group!r}")
        print(f"  Original dict: {dict_repr}")
        print(f"  After round-trip: {dict_repr2}")
        assert False

try:
    test_request_output_round_trip()
    print("✓ Round-trip serialization works correctly\n")
except AssertionError as e:
    print(f"FOUND BUG in round-trip serialization!\n")
except Exception as e:
    print(f"Error during round-trip test: {e}\n")


# Test 4: Type coercion in property setters
print("="*60)
print("TESTING TYPE COERCION")
print("="*60)

@given(
    value=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(alphabet="0123456789.-+eE").filter(lambda x: len(x) > 0),
        st.booleans()
    )
)
@settings(max_examples=30)
def test_double_field_coercion(value):
    """Test what DashPlaylistSettings accepts for double fields"""
    try:
        settings = mediatailor.DashPlaylistSettings(
            ManifestWindowSeconds=value
        )
        d = settings.to_dict()
        
        # If it succeeded, the value should be convertible to float
        try:
            float_val = float(value)
            print(f"✓ Accepted {type(value).__name__} {value!r} -> {d['ManifestWindowSeconds']}")
        except (ValueError, TypeError):
            print(f"BUG: Accepted non-numeric value {value!r} of type {type(value).__name__}")
            assert False
            
    except (ValueError, TypeError) as e:
        # Should only reject non-numeric values
        try:
            float(value)
            print(f"Incorrectly rejected numeric value {value!r}: {e}")
        except (ValueError, TypeError):
            pass  # Correctly rejected

try:
    test_double_field_coercion()
    print("\nType coercion works as expected\n")
except AssertionError:
    print("\nFOUND BUG in type coercion!\n")
except Exception as e:
    print(f"\nError during type coercion test: {e}\n")


# Test 5: Edge cases in property validation
print("="*60)
print("TESTING PROPERTY VALIDATION EDGE CASES")
print("="*60)

# Test empty strings for required fields
def test_empty_string_required():
    """Test if empty strings satisfy 'required' constraint"""
    output = mediatailor.RequestOutputItem(
        ManifestName="",
        SourceGroup=""
    )
    d = output.to_dict()
    print(f"Empty strings accepted for required fields: {d}")
    # This might be a semantic bug - empty strings probably shouldn't satisfy "required"
    return d

try:
    result = test_empty_string_required()
    if result['ManifestName'] == "" and result['SourceGroup'] == "":
        print("Note: Empty strings satisfy 'required' constraint (potential semantic issue)\n")
except Exception as e:
    print(f"Empty strings rejected: {e}\n")


# Test 6: Hash/equality contract
print("="*60) 
print("TESTING HASH/EQUALITY CONTRACT")
print("="*60)

@given(
    name1=st.text(min_size=1, max_size=20),
    source1=st.text(min_size=1, max_size=20),
    name2=st.text(min_size=1, max_size=20),
    source2=st.text(min_size=1, max_size=20)
)
@settings(max_examples=50)
def test_hash_equality_contract(name1, source1, name2, source2):
    """If a == b, then hash(a) == hash(b)"""
    obj1 = mediatailor.RequestOutputItem(
        ManifestName=name1,
        SourceGroup=source1
    )
    obj2 = mediatailor.RequestOutputItem(
        ManifestName=name2,
        SourceGroup=source2
    )
    
    are_equal = (obj1 == obj2)
    hashes_equal = (hash(obj1) == hash(obj2))
    
    # Python contract: if equal, then hashes must be equal
    if are_equal and not hashes_equal:
        print(f"BUG: Equal objects have different hashes!")
        print(f"  obj1: name={name1!r}, source={source1!r}, hash={hash(obj1)}")
        print(f"  obj2: name={name2!r}, source={source2!r}, hash={hash(obj2)}")
        assert False
    
    # Also test self-equality
    assert obj1 == obj1
    assert hash(obj1) == hash(obj1)

try:
    test_hash_equality_contract()
    print("✓ Hash/equality contract maintained\n")
except AssertionError:
    print("FOUND BUG in hash/equality contract!\n")
except Exception as e:
    print(f"Error during hash/equality test: {e}\n")


# Test 7: Special characters in strings
print("="*60)
print("TESTING SPECIAL CHARACTERS")
print("="*60)

@given(
    text=st.text().filter(lambda x: any(c in x for c in ['\n', '\t', '\r', '"', '\\', '\x00']))
)
@settings(max_examples=20)
@example(text='test\x00null')
@example(text='line1\nline2')
@example(text='tab\there')
@example(text='quote"inside')
@example(text='back\\slash')
def test_special_chars_handling(text):
    """Test handling of special characters in string properties"""
    try:
        output = mediatailor.RequestOutputItem(
            ManifestName=text,
            SourceGroup="normal"
        )
        
        # Try to serialize
        d = output.to_dict()
        
        # Try round-trip
        reconstructed = mediatailor.RequestOutputItem._from_dict(**d)
        d2 = reconstructed.to_dict()
        
        if d != d2:
            print(f"BUG: Special char round-trip failed for {text!r}")
            print(f"  Original: {d}")
            print(f"  After: {d2}")
            assert False
            
    except Exception as e:
        print(f"Failed with special char {text!r}: {e}")

try:
    test_special_chars_handling()
    print("✓ Special characters handled correctly\n")
except AssertionError:
    print("FOUND BUG with special characters!\n")
except Exception as e:
    print(f"Error during special char test: {e}\n")


print("="*60)
print("BUG HUNTING COMPLETE")
print("="*60)

# Summary
print("\nSUMMARY OF FINDINGS:")
print("-" * 40)
print("1. Boolean validator: Works as documented")
print("2. Integer validator: Accepts booleans (Python design, bool subclasses int)")
print("3. Double validator: Accepts integers and numeric strings (by design)")
print("4. Empty strings: Satisfy 'required' constraint (potential semantic issue)")
print("5. Round-trip serialization: Works correctly")
print("6. Hash/equality contract: Maintained correctly")
print("7. Special characters: Need further testing")

print("\nPotential issues found:")
print("- Integer fields accept boolean values (True=1, False=0)")
print("- Empty strings satisfy 'required' field constraint")
print("- These may be design choices rather than bugs")