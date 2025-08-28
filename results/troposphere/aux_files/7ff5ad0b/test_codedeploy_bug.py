"""Focused test to demonstrate bug in CodeDeployLambdaAliasUpdate"""

import pytest
from hypothesis import given, strategies as st, settings
import troposphere.policies as policies


@given(st.text(min_size=1).filter(lambda x: x not in ["true", "false", "True", "False", "1", "0"]))
@settings(max_examples=100)
def test_codedeploy_application_name_should_accept_strings(app_name):
    """
    AWS CodeDeploy expects ApplicationName to be a string (the name of the CodeDeploy application).
    However, troposphere.policies.CodeDeployLambdaAliasUpdate uses a boolean validator for this field.
    
    From AWS documentation, ApplicationName should be a string like "MyCodeDeployApp".
    """
    obj = policies.CodeDeployLambdaAliasUpdate()
    
    # This should work (AWS expects strings) but fails due to boolean validator
    with pytest.raises(ValueError):
        obj.ApplicationName = app_name


@given(st.text(min_size=1).filter(lambda x: x not in ["true", "false", "True", "False", "1", "0"]))
@settings(max_examples=100)
def test_codedeploy_deployment_group_name_should_accept_strings(group_name):
    """
    AWS CodeDeploy expects DeploymentGroupName to be a string (the name of the deployment group).
    However, troposphere.policies.CodeDeployLambdaAliasUpdate uses a boolean validator for this field.
    
    From AWS documentation, DeploymentGroupName should be a string like "MyDeploymentGroup".
    """
    obj = policies.CodeDeployLambdaAliasUpdate()
    
    # This should work (AWS expects strings) but fails due to boolean validator
    with pytest.raises(ValueError):
        obj.DeploymentGroupName = group_name


def test_codedeploy_fields_with_real_aws_values():
    """Test with realistic AWS CodeDeploy values that should be accepted"""
    obj = policies.CodeDeployLambdaAliasUpdate()
    
    # These are realistic values from AWS documentation
    realistic_app_names = [
        "MyCodeDeployApplication",
        "prod-lambda-deploy",
        "staging-app",
        "lambda-deployment-app"
    ]
    
    realistic_group_names = [
        "MyDeploymentGroup",
        "prod-deployment-group",
        "canary-deploy-group",
        "blue-green-deployment"
    ]
    
    for app_name in realistic_app_names:
        with pytest.raises(ValueError) as exc_info:
            obj.ApplicationName = app_name
        # The error occurs because boolean validator can't handle these strings
        assert "function validator 'boolean' threw exception" in str(exc_info.value)
    
    for group_name in realistic_group_names:
        with pytest.raises(ValueError) as exc_info:
            obj.DeploymentGroupName = group_name
        assert "function validator 'boolean' threw exception" in str(exc_info.value)