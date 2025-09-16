#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
import pytest
from troposphere.validators import integer

# Bug 1: Integer validator incorrectly accepts booleans and floats
@given(value=st.one_of(st.booleans(), st.floats()))
def test_integer_validator_accepts_non_integers(value):
    """The integer validator should reject booleans and floats but doesn't"""
    result = integer(value)
    # This test shows the bug - integer() returns the original value unchanged
    # for booleans and floats, which is incorrect
    assert result == value  # This passes but shouldn't
    assert type(result) in (bool, float)  # The type is preserved incorrectly


# Bug 2: Tags validator rejects dictionaries
def test_tags_validator_rejects_dicts():
    """The tags_or_list validator should accept dicts but doesn't"""
    from troposphere import appstream
    
    # This should work but raises ValueError
    with pytest.raises(ValueError, match="must be either Tags or list"):
        ab = appstream.AppBlock(
            'TestAppBlock',
            Name='TestBlock',
            SourceS3Location=appstream.S3Location(S3Bucket='bucket', S3Key='key'),
            Tags={'key1': 'value1'}  # Dictionary should be valid
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])