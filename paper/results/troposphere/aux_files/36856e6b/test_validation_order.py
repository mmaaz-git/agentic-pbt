"""Test validation order and error reporting in troposphere.codebuild."""

from troposphere.codebuild import Source, SourceAuth, Artifacts


def test_source_validation_order():
    """Test: Source validation stops at first error, masking other issues."""
    
    # Case 1: CODECOMMIT with Auth (invalid) and no Location (also invalid)
    # Which error gets reported?
    source = Source(Type="CODECOMMIT", Auth=SourceAuth(Type="OAUTH"))
    try:
        source.validate()
        assert False, "Should have raised ValueError"
    except ValueError as e:
        error_msg = str(e)
        print(f"Error for CODECOMMIT with Auth but no Location: {error_msg}")
        
        # The error is about Location, not Auth
        # This means Auth validation is skipped when Location is missing
        assert "Location: must be defined" in error_msg
        
        # Now add Location and see if Auth error appears
        source2 = Source(Type="CODECOMMIT", Location="https://example.com", Auth=SourceAuth(Type="OAUTH"))
        try:
            source2.validate()
            assert False, "Should have raised ValueError for Auth"
        except ValueError as e2:
            error_msg2 = str(e2)
            print(f"Error for CODECOMMIT with Auth and Location: {error_msg2}")
            assert "SourceAuth: must only be defined when using" in error_msg2
            
    return True


def test_artifacts_validation_order():
    """Test: Artifacts S3 validation checks Type first, then Name/Location."""
    
    # Invalid type
    try:
        artifact = Artifacts(Type="INVALID_TYPE")
        artifact.validate()
        assert False, "Should reject invalid type"
    except ValueError as e:
        assert "Artifacts Type: must be one of" in str(e)
    
    # S3 without Name - which property is checked first?
    try:
        artifact = Artifacts(Type="S3", Location="s3://bucket")
        artifact.validate()
        assert False, "Should require Name for S3"
    except ValueError as e:
        error_msg = str(e)
        print(f"S3 without Name error: {error_msg}")
        assert "Name" in error_msg
    
    # S3 without Location
    try:
        artifact = Artifacts(Type="S3", Name="artifact")
        artifact.validate()
        assert False, "Should require Location for S3"
    except ValueError as e:
        error_msg = str(e)
        print(f"S3 without Location error: {error_msg}")
        assert "Location" in error_msg
    
    # S3 with neither Name nor Location - which is reported first?
    try:
        artifact = Artifacts(Type="S3")
        artifact.validate()
        assert False, "Should require both Name and Location for S3"
    except ValueError as e:
        error_msg = str(e)
        print(f"S3 without Name or Location error: {error_msg}")
        # Check which one is reported
        # The code checks Name first
        assert "Name" in error_msg
        
    return True


def test_empty_string_handling():
    """Test: How are empty strings handled in required fields?"""
    
    # Test 1: Empty string for S3 Name
    artifact = Artifacts(Type="S3", Name="", Location="s3://bucket")
    try:
        artifact.validate()
        print("Empty Name string passed validation - potential bug!")
        # Empty string is treated as valid!
        return "BUG_FOUND"
    except ValueError:
        print("Empty Name string correctly rejected")
        
    # Test 2: Empty string for S3 Location  
    artifact2 = Artifacts(Type="S3", Name="artifact", Location="")
    try:
        artifact2.validate()
        print("Empty Location string passed validation - potential bug!")
        return "BUG_FOUND"
    except ValueError:
        print("Empty Location string correctly rejected")
        
    return True


if __name__ == "__main__":
    print("Testing validation order...")
    result1 = test_source_validation_order()
    print(f"Source validation order test: {'PASSED' if result1 else 'FAILED'}\n")
    
    print("Testing artifacts validation order...")
    result2 = test_artifacts_validation_order()
    print(f"Artifacts validation order test: {'PASSED' if result2 else 'FAILED'}\n")
    
    print("Testing empty string handling...")
    result3 = test_empty_string_handling()
    if result3 == "BUG_FOUND":
        print("POTENTIAL BUG: Empty strings are accepted as valid values!")
    else:
        print(f"Empty string handling test: {'PASSED' if result3 else 'FAILED'}")