"""Property-based test that reveals bugs in BinaryCanvas."""

from hypothesis import given, strategies as st, assume
import fire.test_components as tc


# Bug-finding test for BinaryCanvas with invalid sizes
@given(st.integers(min_value=-10, max_value=10))
def test_binary_canvas_size_handling(size):
    """Test that BinaryCanvas handles all integer sizes gracefully."""
    # The constructor should either:
    # 1. Reject invalid sizes (<=0) with a clear error
    # 2. Handle them gracefully throughout all methods
    
    canvas = tc.BinaryCanvas(size)
    
    # All methods should work without crashing
    # Property: If constructor accepts a size, all methods should handle it
    try:
        # move() uses modulo - should not crash
        canvas.move(5, 5)
        
        # Setting pixels should not crash
        canvas.on()
        canvas.off()
        canvas.set(1)
        
        # String representation should not crash
        str(canvas)
        
        # show() should not crash
        canvas.show()
        
    except (ZeroDivisionError, IndexError) as e:
        # These exceptions indicate bugs - the constructor accepted the size
        # but methods can't handle it
        raise AssertionError(
            f"BinaryCanvas({size}) was created successfully but methods failed: {e}"
        )


if __name__ == "__main__":
    # Run with a specific failing case
    test_binary_canvas_size_handling(0)