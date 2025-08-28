import django
from django.conf import settings
settings.configure(DEBUG=True, SECRET_KEY='test')

from django.utils import encoding

# Test various ASCII characters for round-trip
print("Testing IRI/URI round-trip for ASCII characters:")
print("=" * 50)

# Characters that should be percent-encoded in URIs
problematic_chars = ['"', ' ', '<', '>', '{', '}', '|', '\\', '^', '`', '%', '[', ']']

failures = []
for char in problematic_chars:
    uri = encoding.iri_to_uri(char)
    back = encoding.uri_to_iri(uri)
    
    if back != char:
        failures.append((char, uri, back))
        print(f"FAIL: {repr(char)} -> {repr(uri)} -> {repr(back)}")
    else:
        print(f"OK:   {repr(char)} -> {repr(uri)} -> {repr(back)}")

print("\n" + "=" * 50)
print(f"Found {len(failures)} characters that don't round-trip correctly:")
for char, uri, back in failures:
    print(f"  '{char}' becomes '{back}' after round-trip")

# Let's look at the source to understand why
print("\n" + "=" * 50)
print("Looking at the implementation...")
import inspect
print("\niri_to_uri source:")
print(inspect.getsource(encoding.iri_to_uri))
print("\nuri_to_iri source:")
print(inspect.getsource(encoding.uri_to_iri))