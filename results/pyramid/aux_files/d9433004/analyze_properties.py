import sys
import inspect
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.httpexceptions as httpexc

print("=== Analyzing Properties ===\n")

# 1. Check status_map completeness
print("1. Status code mapping:")
print(f"   Number of mapped codes: {len(httpexc.status_map)}")
print(f"   Sample mappings: {list(httpexc.status_map.items())[:5]}")

# Check if all HTTP exception classes have codes
all_exceptions = [
    obj for name, obj in inspect.getmembers(httpexc)
    if inspect.isclass(obj) and issubclass(obj, httpexc.HTTPException) and name.startswith('HTTP')
]
print(f"   Total exception classes: {len(all_exceptions)}")

# 2. Check redirect classes
redirect_classes = [
    obj for name, obj in inspect.getmembers(httpexc)
    if inspect.isclass(obj) and issubclass(obj, httpexc._HTTPMove)
]
print(f"\n2. Redirect exception classes (require location): {len(redirect_classes)}")
for cls in redirect_classes[:3]:
    print(f"   - {cls.__name__}: code={getattr(cls, 'code', None)}")

# 3. Check exception initialization
print("\n3. Exception initialization test:")
try:
    exc = httpexc.HTTPNotFound(detail="Test detail")
    print(f"   HTTPNotFound created: status={exc.status}, detail={exc.detail}")
    print(f"   String representation: {str(exc)}")
except Exception as e:
    print(f"   Error: {e}")

# 4. Test redirect without location
print("\n4. Redirect location requirement:")
try:
    exc = httpexc.HTTPMovedPermanently(location=None)
    print(f"   HTTPMovedPermanently with None location: {exc}")
except ValueError as e:
    print(f"   Expected error for None location: {e}")

# 5. exception_response function
print("\n5. exception_response function:")
try:
    exc = httpexc.exception_response(404, detail="Not found")
    print(f"   exception_response(404) -> {type(exc).__name__}")
    print(f"   Status code: {exc.code}")
except Exception as e:
    print(f"   Error: {e}")