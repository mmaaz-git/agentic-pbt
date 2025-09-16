#!/usr/bin/env python3
"""Property-based test that discovered the Tags bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
import pytest
from troposphere.globalaccelerator import Accelerator
from troposphere import Tags


@given(
    tags=st.dictionaries(
        st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
        st.text(min_size=0, max_size=200),
        max_size=10
    )
)
def test_accelerator_tags_with_common_pattern(tags):
    """Test common pattern for handling optional tags parameter.
    
    This test reveals a bug where the common Python pattern:
        Tags=Tags(tags) if tags else None
    
    fails when tags is an empty dictionary {} because:
    1. Empty dict is falsy in Python, so `if tags` evaluates to False
    2. This sets Tags=None
    3. But Accelerator expects either no Tags property or a Tags object, not None
    """
    # This common pattern should work but doesn't for empty dicts
    acc = Accelerator(
        title="TestAcc",
        Name="TestName",
        Tags=Tags(tags) if tags else None
    )
    
    # Should be able to convert to dict
    dict_repr = acc.to_dict()
    assert "Properties" in dict_repr


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])