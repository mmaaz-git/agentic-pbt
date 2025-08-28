#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pycld2_env/lib/python3.13/site-packages')

import pycld2
import inspect

print("Module:", pycld2)
print("File:", pycld2.__file__)
print("Version:", pycld2.__version__ if hasattr(pycld2, '__version__') else 'N/A')

print("\nModule members:")
for name, obj in inspect.getmembers(pycld2):
    if not name.startswith('_'):
        print(f"  {name}: {type(obj).__name__}")

print("\nDetecting languages:")
print(f"  LANGUAGES: {len(pycld2.LANGUAGES)} languages")
print(f"  DETECTED_LANGUAGES: {len(pycld2.DETECTED_LANGUAGES)} detected languages")
print(f"  ENCODINGS: {len(pycld2.ENCODINGS)} encodings")

print("\nFunction: detect")
if hasattr(pycld2, 'detect'):
    try:
        sig = inspect.signature(pycld2.detect)
        print("  Signature:", sig)
    except ValueError:
        print("  Signature: (builtin - cannot inspect)")
    print("  Docstring:", pycld2.detect.__doc__ if hasattr(pycld2.detect, '__doc__') else "N/A")

print("\nTesting basic functionality:")
result = pycld2.detect("Hello, world!")
print(f"  detect('Hello, world!'): {result}")

print("\nExploring different inputs:")
test_cases = [
    ("Bonjour le monde!", "French"),
    ("Hola mundo!", "Spanish"),
    ("こんにちは世界", "Japanese"),
    ("Привет мир", "Russian"),
    ("مرحبا بالعالم", "Arabic"),
    ("", "Empty string"),
]

for text, description in test_cases:
    try:
        result = pycld2.detect(text)
        print(f"  {description}: {result[0] if result else 'No detection'}")
    except Exception as e:
        print(f"  {description}: Error - {e}")

print("\nChecking some LANGUAGES samples:")
print(f"  First 10 languages: {pycld2.LANGUAGES[:10]}")
print(f"  First 5 detected languages: {pycld2.DETECTED_LANGUAGES[:5]}")
print(f"  First 5 encodings: {pycld2.ENCODINGS[:5]}")