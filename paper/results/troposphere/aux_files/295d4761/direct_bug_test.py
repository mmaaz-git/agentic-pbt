#!/usr/bin/env python3
"""
Direct test to find bugs in troposphere.mediatailor
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

def test_boolean_validator_bug():
    """Test for bug in boolean validator"""
    import troposphere.validators as validators
    
    # According to the implementation in validators/__init__.py lines 38-43:
    # It checks if x in [True, 1, "1", "true", "True"] -> returns True
    # It checks if x in [False, 0, "0", "false", "False"] -> returns False  
    # Otherwise raises ValueError
    
    # This means "1" (string) should return True
    result = validators.boolean("1")
    print(f"boolean('1') = {result}")
    assert result is True, "boolean('1') should return True"
    
    # And "0" (string) should return False
    result = validators.boolean("0")
    print(f"boolean('0') = {result}")
    assert result is False, "boolean('0') should return False"
    
    # Edge case: What about boolean literals as integers?
    # True in Python equals 1, False equals 0
    # So boolean(True) should work
    result = validators.boolean(True)
    print(f"boolean(True) = {result}")
    assert result is True
    
    result = validators.boolean(False)
    print(f"boolean(False) = {result}")
    assert result is False
    
    # But the integer 1 should also work
    result = validators.boolean(1)
    print(f"boolean(1) = {result}")
    assert result is True
    
    result = validators.boolean(0)
    print(f"boolean(0) = {result}")
    assert result is False
    
    print("✓ Boolean validator works as documented")
    return True


def test_integer_validator_with_booleans():
    """Test integer validator with boolean inputs"""
    import troposphere.validators as validators
    
    # In Python, bool is a subclass of int
    # True == 1 and False == 0
    # So int(True) = 1 and int(False) = 0
    
    # The integer validator just does:
    # try: int(x)
    # except (ValueError, TypeError): raise ValueError
    # else: return x
    
    # So it should accept booleans
    result = validators.integer(True)
    print(f"integer(True) = {result}")
    assert result == True
    assert int(result) == 1
    
    result = validators.integer(False) 
    print(f"integer(False) = {result}")
    assert result == False
    assert int(result) == 0
    
    # This might be unexpected behavior - booleans accepted as integers
    print("✓ Integer validator accepts booleans (bool is subclass of int)")
    return True


def test_mediatailor_class_bugs():
    """Test for bugs in mediatailor classes"""
    import troposphere.mediatailor as mediatailor
    
    # Test 1: Can we create objects with None for required fields?
    print("\nTest: RequestOutputItem with None values")
    try:
        output = mediatailor.RequestOutputItem(
            ManifestName=None,
            SourceGroup=None
        )
        # If this succeeds, check if to_dict works
        try:
            d = output.to_dict()
            print(f"BUG: RequestOutputItem accepts None for required fields: {d}")
            return False
        except ValueError as e:
            print(f"to_dict() validation caught None values: {e}")
    except TypeError as e:
        print(f"Constructor rejected None values: {e}")
    
    # Test 2: Empty strings for required fields
    print("\nTest: RequestOutputItem with empty strings")
    output = mediatailor.RequestOutputItem(
        ManifestName="",
        SourceGroup=""
    )
    d = output.to_dict()
    print(f"RequestOutputItem with empty strings: {d}")
    # Empty strings might be technically valid but semantically wrong
    
    # Test 3: Property type coercion
    print("\nTest: DashPlaylistSettings with string for double field")
    settings = mediatailor.DashPlaylistSettings(
        ManifestWindowSeconds="123.45"  # String instead of double
    )
    d = settings.to_dict()
    print(f"DashPlaylistSettings accepts string for double: {d}")
    # The double validator accepts strings that can be converted to float
    
    # Test 4: Integer where double is expected
    settings2 = mediatailor.DashPlaylistSettings(
        ManifestWindowSeconds=100  # Integer instead of double
    )
    d2 = settings2.to_dict()
    print(f"DashPlaylistSettings accepts integer for double: {d2}")
    
    # Test 5: Boolean where integer is expected
    print("\nTest: LogConfiguration with boolean for integer field")
    log_config = mediatailor.LogConfiguration(
        PercentEnabled=True  # Boolean instead of integer
    )
    d = log_config.to_dict()
    print(f"LogConfiguration accepts boolean for integer: {d}")
    # Since bool is subclass of int, this might work
    
    print("✓ Tests completed")
    return True


def test_hash_equality_bug():
    """Test for bugs in __eq__ and __hash__ implementation"""
    import troposphere.mediatailor as mediatailor
    
    print("\nTest: Hash and equality contract")
    
    # Create two identical objects  
    obj1 = mediatailor.RequestOutputItem(
        ManifestName="test",
        SourceGroup="source"
    )
    obj2 = mediatailor.RequestOutputItem(
        ManifestName="test",
        SourceGroup="source"
    )
    
    # Check equality
    are_equal = (obj1 == obj2)
    print(f"obj1 == obj2: {are_equal}")
    
    # Check hashes
    hash1 = hash(obj1)
    hash2 = hash(obj2)
    hashes_equal = (hash1 == hash2)
    print(f"hash(obj1) == hash(obj2): {hashes_equal}")
    
    # Python contract: if a == b, then hash(a) == hash(b)
    if are_equal and not hashes_equal:
        print("BUG FOUND: Equal objects have different hashes!")
        print(f"  hash(obj1) = {hash1}")
        print(f"  hash(obj2) = {hash2}")
        return False
    
    print("✓ Hash/equality contract maintained")
    return True


if __name__ == "__main__":
    print("Testing troposphere.mediatailor for bugs...")
    print("="*60)
    
    bugs_found = []
    
    try:
        if not test_boolean_validator_bug():
            bugs_found.append("boolean_validator")
    except Exception as e:
        print(f"Error in boolean validator test: {e}")
        bugs_found.append("boolean_validator_error")
    
    print("\n" + "="*60)
    
    try:
        if not test_integer_validator_with_booleans():
            bugs_found.append("integer_validator")
    except Exception as e:
        print(f"Error in integer validator test: {e}")
        bugs_found.append("integer_validator_error")
    
    print("\n" + "="*60)
    
    try:
        if not test_mediatailor_class_bugs():
            bugs_found.append("mediatailor_classes")
    except Exception as e:
        print(f"Error in mediatailor class test: {e}")
        bugs_found.append("mediatailor_classes_error")
    
    print("\n" + "="*60)
    
    try:
        if not test_hash_equality_bug():
            bugs_found.append("hash_equality")
    except Exception as e:
        print(f"Error in hash/equality test: {e}")
        bugs_found.append("hash_equality_error")
    
    print("\n" + "="*60)
    print("SUMMARY:")
    if bugs_found:
        print(f"Found potential bugs in: {', '.join(bugs_found)}")
    else:
        print("No bugs found in basic tests")
    
    # Now let's try to trigger actual bugs
    print("\n" + "="*60)
    print("ATTEMPTING TO FIND ACTUAL BUGS:")
    print("="*60)
    
    import troposphere.mediatailor as mediatailor
    
    # Bug attempt 1: Type confusion with validators
    print("\nBug Hunt 1: Type confusion in validators")
    import troposphere.validators as validators
    
    # The boolean validator uses == comparison in lists
    # What if we pass something that equals True/1 but isn't in the list?
    class AlwaysOne:
        def __eq__(self, other):
            return other == 1
    
    try:
        result = validators.boolean(AlwaysOne())
        print(f"BUG: boolean(AlwaysOne()) = {result}")
    except ValueError:
        print("OK: boolean validator rejected AlwaysOne()")
    
    # Bug attempt 2: Round-trip with special values
    print("\nBug Hunt 2: Round-trip serialization")
    
    output = mediatailor.RequestOutputItem(
        ManifestName="test\nwith\nnewlines",
        SourceGroup="source\twith\ttabs"
    )
    d = output.to_dict()
    print(f"Serialized special chars: {d}")
    
    # Try to reconstruct - this might fail if escaping is wrong
    try:
        reconstructed = mediatailor.RequestOutputItem._from_dict(**d)
        d2 = reconstructed.to_dict()
        if d == d2:
            print("Round-trip with special chars succeeded")
        else:
            print(f"BUG: Round-trip failed!")
            print(f"  Original: {d}")
            print(f"  After round-trip: {d2}")
    except Exception as e:
        print(f"Round-trip failed with error: {e}")