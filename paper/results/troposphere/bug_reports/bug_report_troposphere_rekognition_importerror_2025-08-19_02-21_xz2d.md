# Bug Report: troposphere.rekognition Missing Point Class ImportError

**Target**: `troposphere.rekognition.validate_PolygonRegionsOfInterest`
**Severity**: High
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `validate_PolygonRegionsOfInterest` function fails with ImportError because it tries to import a non-existent `Point` class from `troposphere.rekognition`.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.rekognition as rek

@given(st.lists(st.lists(st.integers())))
def test_validate_polygon_regions_crashes(polygons):
    """Test that validate_PolygonRegionsOfInterest always crashes due to missing Point class"""
    try:
        rek.validate_PolygonRegionsOfInterest(polygons)
        assert False, "Expected ImportError but validation succeeded"
    except ImportError as e:
        assert "cannot import name 'Point'" in str(e)
    except TypeError:
        pass  # Expected for invalid input types
```

**Failing input**: `[[]]` (or any list input)

## Reproducing the Bug

```python
import troposphere.rekognition as rek

# Any call to validate_PolygonRegionsOfInterest fails
rek.validate_PolygonRegionsOfInterest([[]])
```

## Why This Is A Bug

The validation function is completely broken and cannot be used at all. It references a `Point` class that doesn't exist in the module, making the `PolygonRegionsOfInterest` property of `StreamProcessor` unusable.

## Fix

Define the missing Point class or update the import statement to reference the correct module. Based on the validation logic, Point should be an AWSProperty with X and Y coordinates:

```diff
+class Point(AWSProperty):
+    """Point for PolygonRegionsOfInterest"""
+    props: PropsDictType = {
+        "X": (double, True),
+        "Y": (double, True),
+    }
+
 def validate_PolygonRegionsOfInterest(polygons):
     """
     Property: StreamProcessor.PolygonRegionsOfInterest
     """
-    from ..rekognition import Point
+    # Point is now defined in this module
 
     if not isinstance(polygons, list):
         raise TypeError("PolygonRegionsOfInterest must be a list")
```