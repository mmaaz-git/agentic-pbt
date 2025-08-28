# Bug Report: troposphere.BaseAWSObject None Title Causes TypeError in Template Serialization

**Target**: `troposphere.BaseAWSObject`
**Severity**: Medium  
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

BaseAWSObject allows None or empty string titles which bypass validation but cause TypeError when multiple resources are added to a Template and it attempts to sort them during serialization.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.paymentcryptography import Alias

@given(st.text())
def test_alias_title_validation(title):
    """Test that Alias title must be alphanumeric."""
    is_valid = title and all(c.isalnum() for c in title)
    
    if is_valid:
        alias = Alias(title, AliasName='test')
        assert alias.title == title
    else:
        with pytest.raises(ValueError, match=r'Name .* not alphanumeric'):
            Alias(title, AliasName='test')
```

**Failing input**: `''` (empty string) and `None`

## Reproducing the Bug

```python
from troposphere import Template
from troposphere.paymentcryptography import Alias

# Create aliases - one with None title, one with valid title
alias1 = Alias(None, AliasName='test-alias-1')
alias2 = Alias('ValidName', AliasName='test-alias-2')

# Add to template
template = Template()
template.add_resource(alias1)
template.add_resource(alias2)

# Try to serialize - crashes when sorting resources
json_output = template.to_json()  # TypeError: '<' not supported between instances of 'str' and 'NoneType'
```

## Why This Is A Bug

The BaseAWSObject.__init__ only validates titles if they are truthy: `if self.title: self.validate_title()`. This allows None and empty string titles to bypass validation. While this might seem like optional titles are supported, it causes crashes when Templates try to sort resources by title during JSON serialization. Resources must have valid alphanumeric titles for CloudFormation templates to work correctly.

## Fix

```diff
def __init__(self, title: Optional[str], template: Optional[Template] = None, validation: bool = True, **kwargs: Any) -> None:
    self.title = title
    self.template = template
    self.do_validation = validation
    # Cache the keys for validity checks
    self.propnames = set(self.props.keys())
    self.attributes = [...]
    
    # try to validate the title if its there
-   if self.title:
-       self.validate_title()
+   # Always validate title for objects that require it (resource objects)
+   if hasattr(self, 'resource_type'):
+       self.validate_title()
```