# Bug Report: troposphere.opsworks Invalid Iops Validation Logic

**Target**: `troposphere.validators.opsworks.validate_volume_configuration`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `validate_volume_configuration` function incorrectly rejects Iops when VolumeType is not specified (None), treating it the same as non-io1 volume types.

## Property-Based Test

```python
@given(
    volume_type=st.sampled_from(["standard", "io1", "gp2", None]),
    iops=st.one_of(st.none(), st.integers(min_value=1, max_value=20000)),
    mount_point=st.text(min_size=1, max_size=100),
)
def test_validate_volume_configuration_iops_constraint(volume_type, iops, mount_point):
    """Test that Iops is required iff VolumeType is 'io1'."""
    
    class MockVolumeConfig:
        def __init__(self):
            self.properties = {}
            if volume_type is not None:
                self.properties["VolumeType"] = volume_type
            if iops is not None:
                self.properties["Iops"] = iops
            self.properties["MountPoint"] = mount_point
    
    config = MockVolumeConfig()
    
    should_raise = False
    if volume_type == "io1" and iops is None:
        should_raise = True
    elif volume_type != "io1" and volume_type is not None and iops is not None:
        should_raise = True
    
    if should_raise:
        with pytest.raises(ValueError):
            opsworks_validators.validate_volume_configuration(config)
    else:
        opsworks_validators.validate_volume_configuration(config)
```

**Failing input**: `volume_type=None, iops=1, mount_point='0'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators.opsworks import validate_volume_configuration

class MockVolumeConfig:
    def __init__(self):
        self.properties = {"Iops": 100}

config = MockVolumeConfig()
validate_volume_configuration(config)
```

## Why This Is A Bug

VolumeType is an optional property in VolumeConfiguration (marked as False in the props definition). When VolumeType is not specified, the validation should not enforce the Iops constraint. The current implementation treats `VolumeType=None` the same as `VolumeType="standard"` or `VolumeType="gp2"`, which incorrectly rejects valid configurations where Iops is specified without an explicit VolumeType.

## Fix

```diff
def validate_volume_configuration(self):
    """
    Class: VolumeConfiguration
    """

    volume_type = self.properties.get("VolumeType")
    iops = self.properties.get("Iops")
    if volume_type == "io1" and not iops:
        raise ValueError("Must specify Iops if VolumeType is 'io1'.")
-   if volume_type != "io1" and iops:
+   if volume_type is not None and volume_type != "io1" and iops:
        raise ValueError("Cannot specify Iops if VolumeType is not 'io1'.")
```