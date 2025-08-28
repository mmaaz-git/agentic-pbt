"""Focused test for ByteSize.human_readable() precision loss bug"""

from hypothesis import given, strategies as st, settings
from pydantic import BaseModel
from pydantic.types import ByteSize


@given(st.integers(min_value=1024**3, max_value=10 * 1024**3))  # 1 GiB to 10 GiB
@settings(max_examples=1000)
def test_bytesize_human_readable_precision_loss(value):
    """ByteSize.human_readable() should not lose more than 1% precision"""
    class Model(BaseModel):
        size: ByteSize
    
    # Create ByteSize from integer
    m1 = Model(size=value)
    
    # Get human readable representation
    human = m1.size.human_readable()
    
    # Parse it back
    m2 = Model(size=human)
    parsed_value = int(m2.size)
    
    # Calculate precision loss
    if parsed_value != value:
        loss_ratio = abs(value - parsed_value) / value
        # We found values with up to 2.91% loss, which is unacceptable
        # A reasonable threshold would be 1% for human-readable representations
        assert loss_ratio < 0.01, f"Precision loss of {loss_ratio*100:.2f}% is too high: {value} -> {human} -> {parsed_value}"


if __name__ == "__main__":
    # Run the test
    test_bytesize_human_readable_precision_loss()