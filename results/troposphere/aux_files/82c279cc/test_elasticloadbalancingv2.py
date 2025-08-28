"""Property-based tests for troposphere.elasticloadbalancingv2 module"""

import re
from hypothesis import given, strategies as st, assume, settings
import pytest
import troposphere.elasticloadbalancingv2 as elbv2
from troposphere import validators


# Test 1: validate_network_port property
@given(st.integers())
def test_network_port_accepts_valid_rejects_invalid(port):
    """Test that network_port validator accepts 0-65535 and rejects others"""
    if -1 <= port <= 65535:
        # Should accept valid ports
        result = elbv2.validate_network_port(port)
        assert result == port
    else:
        # Should reject invalid ports
        with pytest.raises(ValueError, match="must been between 0 and 65535"):
            elbv2.validate_network_port(port)


@given(st.text())
def test_tg_healthcheck_port_traffic_port_special_case(text):
    """Test that tg_healthcheck_port accepts 'traffic-port' as special case"""
    if text == "traffic-port":
        result = elbv2.tg_healthcheck_port(text)
        assert result == "traffic-port"
    elif text.isdigit():
        port = int(text)
        if -1 <= port <= 65535:
            result = elbv2.tg_healthcheck_port(text)
            assert result == text
        else:
            with pytest.raises(ValueError):
                elbv2.tg_healthcheck_port(text)
    else:
        # Non-numeric strings (except "traffic-port") should raise
        with pytest.raises((ValueError, TypeError)):
            elbv2.tg_healthcheck_port(text)


# Test 2: validate_elb_name property
@given(st.text())
def test_elb_name_regex_validation(name):
    """Test ELB name validation against its regex pattern"""
    # The regex: ^[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,30}[a-zA-Z0-9]{1})?$
    # This means:
    # - Must start with alphanumeric
    # - Can have 0-30 chars of alphanumeric or dash in middle
    # - Must end with alphanumeric if length > 1
    # - Total length 1-32 chars
    
    pattern = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,30}[a-zA-Z0-9]{1})?$")
    
    if pattern.match(name):
        # Should accept valid names
        result = elbv2.validate_elb_name(name)
        assert result == name
    else:
        # Should reject invalid names
        with pytest.raises(ValueError, match="is not a valid elb name"):
            elbv2.validate_elb_name(name)


# Test 3: validate_target_type property
@given(st.text())
def test_target_type_only_accepts_valid_types(target_type):
    """Test that validate_target_type only accepts the 4 valid types"""
    valid_types = ['alb', 'instance', 'ip', 'lambda']
    
    if target_type in valid_types:
        result = elbv2.validate_target_type(target_type)
        assert result == target_type
    else:
        with pytest.raises(ValueError, match='TargetGroup.TargetType must be one of'):
            elbv2.validate_target_type(target_type)


# Test 4: Action class type-specific requirements
@given(
    st.sampled_from(['forward', 'redirect', 'fixed-response', 
                     'authenticate-cognito', 'authenticate-oidc']),
    st.booleans(),  # include TargetGroupArn
    st.booleans(),  # include ForwardConfig
    st.booleans(),  # include RedirectConfig
    st.booleans(),  # include FixedResponseConfig
)
def test_action_type_specific_requirements(action_type, has_target_group, 
                                          has_forward, has_redirect, has_fixed):
    """Test Action class enforces type-specific property requirements"""
    
    # Build kwargs based on flags
    kwargs = {'Type': action_type}
    
    if has_target_group:
        kwargs['TargetGroupArn'] = 'test-arn'
    if has_forward:
        kwargs['ForwardConfig'] = elbv2.ForwardConfig()
    if has_redirect:
        kwargs['RedirectConfig'] = elbv2.RedirectConfig(StatusCode='HTTP_301')
    if has_fixed:
        kwargs['FixedResponseConfig'] = elbv2.FixedResponseConfig(
            StatusCode='200',
            ContentType='text/plain'
        )
    
    # Check if this combination should be valid
    should_be_valid = True
    error_msg = None
    
    # Forward type requires either TargetGroupArn or ForwardConfig
    if action_type == 'forward':
        if not (has_target_group or has_forward):
            should_be_valid = False
            error_msg = 'Type "forward" requires definition'
        # Can't have redirect or fixed-response configs with forward
        if has_redirect:
            should_be_valid = False
            error_msg = 'Definition of ".*RedirectConfig.*" allowed only with.*type "redirect"'
        if has_fixed:
            should_be_valid = False
            error_msg = 'Definition of ".*FixedResponseConfig.*" allowed only with.*type "fixed-response"'
    
    # Redirect type requires RedirectConfig
    elif action_type == 'redirect':
        if not has_redirect:
            should_be_valid = False
            error_msg = 'Type "redirect" requires definition'
        # Can't have forward or fixed configs with redirect
        if has_target_group or has_forward:
            should_be_valid = False
            error_msg = 'Definition of ".*(?:TargetGroupArn|ForwardConfig).*" allowed only with.*type "forward"'
        if has_fixed:
            should_be_valid = False
            error_msg = 'Definition of ".*FixedResponseConfig.*" allowed only with.*type "fixed-response"'
    
    # Fixed-response type requires FixedResponseConfig
    elif action_type == 'fixed-response':
        if not has_fixed:
            should_be_valid = False
            error_msg = 'Type "fixed-response" requires definition'
        # Can't have forward or redirect configs with fixed-response
        if has_target_group or has_forward:
            should_be_valid = False
            error_msg = 'Definition of ".*(?:TargetGroupArn|ForwardConfig).*" allowed only with.*type "forward"'
        if has_redirect:
            should_be_valid = False
            error_msg = 'Definition of ".*RedirectConfig.*" allowed only with.*type "redirect"'
    
    # Auth types don't require these configs
    else:  # authenticate-cognito or authenticate-oidc
        # Can't have forward, redirect, or fixed configs with auth types
        if has_target_group or has_forward:
            should_be_valid = False
            error_msg = 'Definition of ".*(?:TargetGroupArn|ForwardConfig).*" allowed only with.*type "forward"'
        if has_redirect:
            should_be_valid = False
            error_msg = 'Definition of ".*RedirectConfig.*" allowed only with.*type "redirect"'
        if has_fixed:
            should_be_valid = False
            error_msg = 'Definition of ".*FixedResponseConfig.*" allowed only with.*type "fixed-response"'
    
    # Try to create the Action
    if should_be_valid:
        action = elbv2.Action(**kwargs)
        action.validate()  # Should not raise
    else:
        with pytest.raises(ValueError, match=error_msg):
            action = elbv2.Action(**kwargs)
            action.validate()


# Test 5: TargetGroup targettype-specific requirements
@given(
    st.sampled_from([None, 'instance', 'ip', 'lambda', 'alb']),
    st.booleans(),  # include Port
    st.booleans(),  # include Protocol  
    st.booleans(),  # include VpcId
)
def test_targetgroup_targettype_requirements(target_type, has_port, has_protocol, has_vpc):
    """Test TargetGroup enforces targettype-specific property requirements"""
    
    kwargs = {}
    if target_type is not None:
        kwargs['TargetType'] = target_type
    
    if has_port:
        kwargs['Port'] = 80
    if has_protocol:
        kwargs['Protocol'] = 'HTTP'
    if has_vpc:
        kwargs['VpcId'] = 'vpc-12345'
    
    # Determine if this should be valid
    should_be_valid = True
    error_msg = None
    
    # None, instance, and ip require Port, Protocol, and VpcId
    if target_type in [None, 'instance', 'ip']:
        if not (has_port and has_protocol and has_vpc):
            should_be_valid = False
            error_msg = 'requires definitions of'
    # lambda must NOT have Port, Protocol, or VpcId
    elif target_type == 'lambda':
        if has_port or has_protocol or has_vpc:
            should_be_valid = False
            error_msg = 'must not contain definitions of'
    # alb type isn't mentioned in the validation, so it may pass
    
    # Try to create the TargetGroup
    if should_be_valid:
        tg = elbv2.TargetGroup('TestTG', **kwargs)
        tg.validate()  # Should not raise
    else:
        with pytest.raises(ValueError, match=error_msg):
            tg = elbv2.TargetGroup('TestTG', **kwargs)
            tg.validate()


# Test 6: Round-trip property with to_dict
@given(
    st.sampled_from(['forward', 'redirect', 'fixed-response']),
    st.integers(min_value=1, max_value=50000)
)
def test_action_to_dict_preserves_properties(action_type, order):
    """Test that Action objects preserve properties through to_dict"""
    
    # Create valid Action based on type
    if action_type == 'forward':
        action = elbv2.Action(
            Type=action_type,
            Order=order,
            TargetGroupArn='arn:aws:elasticloadbalancing:test'
        )
    elif action_type == 'redirect':
        action = elbv2.Action(
            Type=action_type,
            Order=order,
            RedirectConfig=elbv2.RedirectConfig(
                StatusCode='HTTP_301',
                Host='example.com'
            )
        )
    else:  # fixed-response
        action = elbv2.Action(
            Type=action_type,
            Order=order,
            FixedResponseConfig=elbv2.FixedResponseConfig(
                StatusCode='200',
                ContentType='text/plain',
                MessageBody='OK'
            )
        )
    
    # Convert to dict and check properties are preserved
    result = action.to_dict()
    
    assert result['Type'] == action_type
    assert result['Order'] == order
    
    # Check type-specific properties
    if action_type == 'forward':
        assert 'TargetGroupArn' in result
    elif action_type == 'redirect':
        assert 'RedirectConfig' in result
        assert result['RedirectConfig']['StatusCode'] == 'HTTP_301'
    else:  # fixed-response
        assert 'FixedResponseConfig' in result
        assert result['FixedResponseConfig']['StatusCode'] == '200'


# Test 7: LoadBalancer name validation through class
@given(st.text())
def test_loadbalancer_name_validation(name):
    """Test LoadBalancer name validation when creating instances"""
    pattern = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,30}[a-zA-Z0-9]{1})?$")
    
    # LoadBalancer uses validate_elb_name for its Name property
    kwargs = {'Name': name}
    
    if pattern.match(name):
        # Should create successfully
        lb = elbv2.LoadBalancer('TestLB', **kwargs)
        assert lb.properties['Name'] == name
    else:
        # Should reject invalid names
        with pytest.raises(ValueError, match="is not a valid elb name"):
            lb = elbv2.LoadBalancer('TestLB', **kwargs)


# Test 8: TargetGroup Port validation
@given(st.integers())
def test_targetgroup_port_validation(port):
    """Test TargetGroup Port property validation"""
    
    # TargetGroup requires Port, Protocol, VpcId for non-lambda types
    kwargs = {
        'Port': port,
        'Protocol': 'HTTP',
        'VpcId': 'vpc-12345',
        'TargetType': 'instance'
    }
    
    if -1 <= port <= 65535:
        # Should create successfully
        tg = elbv2.TargetGroup('TestTG', **kwargs)
        assert tg.properties['Port'] == port
    else:
        # Should reject invalid ports
        with pytest.raises(ValueError, match="must been between 0 and 65535"):
            tg = elbv2.TargetGroup('TestTG', **kwargs)


# Test 9: Listener with multiple properties
@given(
    st.integers(),
    st.sampled_from(['HTTP', 'HTTPS', 'TCP', 'TLS', 'UDP', 'TCP_UDP'])
)
def test_listener_port_and_protocol(port, protocol):
    """Test Listener creation with Port and Protocol"""
    
    # Listener requires LoadBalancerArn and DefaultActions
    kwargs = {
        'LoadBalancerArn': 'arn:aws:elasticloadbalancing:test',
        'DefaultActions': [
            elbv2.Action(Type='forward', TargetGroupArn='test-arn')
        ]
    }
    
    # Add optional Port and Protocol
    if -1 <= port <= 65535:
        kwargs['Port'] = port
        kwargs['Protocol'] = protocol
        
        listener = elbv2.Listener('TestListener', **kwargs)
        assert listener.properties.get('Port') == port
        assert listener.properties.get('Protocol') == protocol
    else:
        kwargs['Port'] = port
        with pytest.raises(ValueError, match="must been between 0 and 65535"):
            listener = elbv2.Listener('TestListener', **kwargs)


# Test 10: RedirectConfig StatusCode validation
@given(st.text())
def test_redirect_config_status_code(status_code):
    """Test RedirectConfig StatusCode must be HTTP_301 or HTTP_302"""
    
    if status_code in ['HTTP_301', 'HTTP_302']:
        config = elbv2.RedirectConfig(StatusCode=status_code)
        config.validate()  # Should not raise
        assert config.properties['StatusCode'] == status_code
    else:
        # Should require one of the valid status codes
        config = elbv2.RedirectConfig(StatusCode=status_code)
        with pytest.raises(ValueError, match='must contain one of'):
            config.validate()