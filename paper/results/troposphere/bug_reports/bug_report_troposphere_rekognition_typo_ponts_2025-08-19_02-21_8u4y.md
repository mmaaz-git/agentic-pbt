# Bug Report: troposphere.rekognition Typo in Error Message

**Target**: `troposphere.rekognition.validate_PolygonRegionsOfInterest`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The error message in `validate_PolygonRegionsOfInterest` contains a typo: "ponts" instead of "points".

## Property-Based Test

```python
import troposphere.rekognition as rek

def test_validate_polygon_error_message_typo():
    """Test that the error message contains a typo 'ponts' instead of 'points'"""
    import types
    
    # Create a fake Point class to bypass ImportError
    class FakePoint:
        pass
    
    rek.Point = FakePoint
    
    try:
        rek.validate_PolygonRegionsOfInterest([['not points']])
    except TypeError as e:
        assert 'ponts' in str(e)
        assert 'points' not in str(e)
    finally:
        delattr(rek, 'Point')
```

**Failing input**: Any list of lists containing non-Point objects

## Reproducing the Bug

```python
import inspect
import troposphere.rekognition as rek

# View the source code showing the typo
source = inspect.getsource(rek.validate_PolygonRegionsOfInterest)
print("Line with typo:")
for line in source.split('\n'):
    if 'ponts' in line:
        print(line)
# Output: raise TypeError("PolygonRegionsOfInterest must be a list of lists of ponts")
```

## Why This Is A Bug

The typo makes error messages less professional and potentially confusing to users who might wonder what "ponts" are.

## Fix

Correct the spelling in the error message:

```diff
     all_points = all(
         isinstance(point, Point) for sublist in polygons for point in sublist
     )
     if not all_points:
-        raise TypeError("PolygonRegionsOfInterest must be a list of lists of ponts")
+        raise TypeError("PolygonRegionsOfInterest must be a list of lists of points")
```