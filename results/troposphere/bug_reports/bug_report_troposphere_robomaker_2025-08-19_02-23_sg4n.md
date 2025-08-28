# Bug Report: troposphere.robomaker Missing Required Title Parameter

**Target**: `troposphere.robomaker`
**Severity**: High
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

AWSObject subclasses in troposphere.robomaker require an undocumented 'title' parameter, causing instantiation to fail when following expected API patterns.

## Property-Based Test

```python
@given(
    name=st.one_of(st.none(), aws_name_strategy),
    tags=st.one_of(st.none(), st.dictionaries(
        keys=aws_name_strategy,
        values=aws_name_strategy,
        min_size=0,
        max_size=5
    ))
)
def test_fleet_with_tags(name, tags):
    """Test Fleet class with optional tags"""
    kwargs = {}
    if name:
        kwargs['Name'] = name
    if tags:
        kwargs['Tags'] = tags
    
    fleet = robomaker.Fleet(**kwargs)
    fleet.validate()
    dict_repr = fleet.to_dict()
    
    if name:
        assert dict_repr['Name'] == name
    if tags:
        assert dict_repr['Tags'] == tags
```

**Failing input**: `name=None, tags=None`

## Reproducing the Bug

```python
import troposphere.robomaker as robomaker

fleet = robomaker.Fleet(Name='TestFleet')
```

## Why This Is A Bug

The API contract is violated in multiple ways:
1. The 'title' parameter is not documented in the module
2. It's not listed in the class's `props` attribute
3. The signature shows `title: Optional[str]` but it's actually required
4. This breaks the expected instantiation pattern where users pass CloudFormation properties directly

Users expect to create resources by passing CloudFormation properties as kwargs, but instead get: `TypeError: BaseAWSObject.__init__() missing 1 required positional argument: 'title'`

## Fix

The title parameter should either be:
1. Made truly optional with a default value
2. Clearly documented as a required positional argument
3. Auto-generated from the resource name if not provided

```diff
class BaseAWSObject(BaseAWSObject):
    def __init__(
-       self, title: Optional[str], template: Optional[Template] = None,
+       self, title: Optional[str] = None, template: Optional[Template] = None,
        validation: bool = True, **kwargs: Any
    ) -> None:
+       if title is None:
+           title = f"{self.__class__.__name__}_{id(self)}"
        self.title = title
```