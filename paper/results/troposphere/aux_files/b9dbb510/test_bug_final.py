"""Final test demonstrating the numeric string key bug in troposphere.evidently"""

import troposphere.evidently as evidently
import pytest


def test_numeric_string_kwargs_bug():
    """
    Bug: AWS classes in troposphere.evidently raise confusing AttributeError 
    when passed kwargs with numeric string keys.
    """
    # Minimal failing example
    with pytest.raises(AttributeError) as exc_info:
        evidently.VariationObject(**{'0': 'value'})
    
    assert "does not support attribute 0" in str(exc_info.value)
    
    # This affects all AWS classes
    classes_with_bug = [
        evidently.VariationObject,
        evidently.EntityOverride, 
        evidently.MetricGoalObject,
        evidently.TreatmentToWeight,
        evidently.S3Destination,
        evidently.Experiment,
        evidently.Feature,
        evidently.Launch,
        evidently.Project,
        evidently.Segment
    ]
    
    for cls in classes_with_bug:
        with pytest.raises(AttributeError) as exc_info:
            if cls in [evidently.Experiment, evidently.Feature, evidently.Launch, 
                       evidently.Project, evidently.Segment]:
                # These require a title
                cls('TestTitle', **{'123': 'test'})
            else:
                cls(**{'123': 'test'})
        assert "does not support attribute 123" in str(exc_info.value)


if __name__ == "__main__":
    test_numeric_string_kwargs_bug()
    print("Bug confirmed: All AWS classes fail with numeric string kwargs")