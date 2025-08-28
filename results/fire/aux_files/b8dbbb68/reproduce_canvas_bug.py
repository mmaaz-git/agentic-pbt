"""Minimal reproduction of BinaryCanvas bug"""

import fire.test_components as target

# Create a canvas of size 1
canvas = target.BinaryCanvas(size=1)
print(f"Canvas size: 1x1")
print(f"Initial pixels: {canvas.pixels}")

# Move to position (1, 1) - should wrap to (0, 0) with modulo
canvas.move(1, 1)
print(f"\nAfter move(1, 1):")
print(f"Internal cursor position: row={canvas._row}, col={canvas._col}")

# Try to set a value at this position
canvas.on()
print(f"After on(): pixels={canvas.pixels}")

# Now move to (2, 2) - should also wrap to (0, 0)
canvas.move(2, 2)
print(f"\nAfter move(2, 2):")  
print(f"Internal cursor position: row={canvas._row}, col={canvas._col}")

# The issue in my test: I was checking pixels[1][1] directly
# But with size=1, pixels only has pixels[0][0]
print(f"\nCanvas dimensions: {len(canvas.pixels)}x{len(canvas.pixels[0])}")
print("Trying to access pixels[1][1]...")
try:
    value = canvas.pixels[1][1]
    print(f"pixels[1][1] = {value}")
except IndexError as e:
    print(f"ERROR: {e}")
    print("This is the bug - my test assumed pixels[1][1] exists even when size=1")