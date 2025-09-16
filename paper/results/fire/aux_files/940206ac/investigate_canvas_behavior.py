"""Investigate BinaryCanvas behavior with size=1"""

import fire.test_components as target

canvas = target.BinaryCanvas(size=1)
print("Canvas size: 1x1")
print(f"Initial state: pixels={canvas.pixels}")

# When size=1, both (1,1) and (2,2) wrap to (0,0)
print("\nStep 1: move(1,1).on()")
canvas.move(1, 1).on()
print(f"After move(1,1).on(): row={canvas._row}, col={canvas._col}, pixels={canvas.pixels}")

print("\nStep 2: move(2,2).off()")
canvas.move(2, 2).off()
print(f"After move(2,2).off(): row={canvas._row}, col={canvas._col}, pixels={canvas.pixels}")

print("\nAnalysis:")
print("- move(1,1) with size=1 wraps to position (0,0)")
print("- move(2,2) with size=1 also wraps to position (0,0)")
print("- So we're turning the same pixel on then off")
print("- Final state should be 0, which is what we observe")
print("\nThis is correct behavior, not a bug!")