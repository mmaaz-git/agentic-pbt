"""Investigate BinaryCanvas negative size bug"""

import fire.test_components as target

# Test various invalid sizes
test_sizes = [-5, -1, 0]

for size in test_sizes:
    print(f"\nTesting BinaryCanvas with size={size}")
    try:
        canvas = target.BinaryCanvas(size=size)
        print(f"  Canvas created successfully!")
        print(f"  pixels dimensions: {len(canvas.pixels)}x{len(canvas.pixels[0]) if canvas.pixels else 'N/A'}")
        print(f"  pixels content: {canvas.pixels}")
        print(f"  _size field: {canvas._size}")
        
        # Try to use the canvas
        try:
            canvas.move(0, 0)
            print(f"  move(0,0) succeeded: row={canvas._row}, col={canvas._col}")
        except Exception as e:
            print(f"  move(0,0) failed: {e}")
            
        try:
            canvas.on()
            print(f"  on() succeeded")
        except Exception as e:
            print(f"  on() failed: {e}")
            
    except Exception as e:
        print(f"  Failed to create canvas: {type(e).__name__}: {e}")

print("\n\nAnalysis:")
print("BinaryCanvas accepts negative and zero sizes without validation.")
print("This creates an empty pixel array, which can cause issues:")
print("- move() with modulo by negative/zero will fail")
print("- Setting pixels will fail with IndexError")
print("This is a bug - the constructor should validate size > 0")