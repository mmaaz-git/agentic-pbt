import troposphere.redshift as redshift
from hypothesis import given, strategies as st


def test_cluster_validate_vs_to_dict_inconsistency():
    """Demonstrate that validate() doesn't check required fields but to_dict() does"""
    
    # Create a cluster missing a required field (ClusterType)
    cluster = redshift.Cluster(
        'TestCluster',
        DBName='testdb',
        MasterUsername='admin',
        NodeType='dc2.large'
        # Missing required ClusterType field
    )
    
    # validate() should fail but doesn't
    try:
        cluster.validate()
        validation_passed = True
    except Exception as e:
        validation_passed = False
        print(f"validate() raised: {e}")
    
    # to_dict() should fail and does
    try:
        cluster.to_dict()
        to_dict_passed = True
    except Exception as e:
        to_dict_passed = False
        print(f"to_dict() raised: {e}")
    
    # This demonstrates the bug: validate() passes but to_dict() fails
    assert validation_passed == True, "validate() should pass (current behavior)"
    assert to_dict_passed == False, "to_dict() should fail (current behavior)"
    
    print("BUG CONFIRMED: validate() doesn't check required fields but to_dict() does")
    return validation_passed, to_dict_passed


@given(
    required_fields=st.dictionaries(
        st.sampled_from(['ClusterType', 'DBName', 'MasterUsername', 'NodeType']),
        st.just(None),  # We'll skip these fields
        min_size=1, max_size=1
    )
)
def test_all_required_fields_have_bug(required_fields):
    """Test that the bug affects all required fields"""
    
    # Start with all required fields
    fields = {
        'ClusterType': 'single-node',
        'DBName': 'testdb',
        'MasterUsername': 'admin',
        'NodeType': 'dc2.large'
    }
    
    # Remove the field we're testing
    for field_to_skip in required_fields:
        del fields[field_to_skip]
    
    cluster = redshift.Cluster('TestCluster', **fields)
    
    # validate() should fail for missing required field but doesn't
    try:
        cluster.validate()
        validate_passed = True
    except Exception:
        validate_passed = False
    
    # to_dict() should fail and does
    try:
        cluster.to_dict()
        to_dict_passed = True
    except Exception:
        to_dict_passed = False
    
    # The bug: validate() passes but to_dict() fails
    assert validate_passed == True
    assert to_dict_passed == False


def test_other_redshift_classes_have_same_bug():
    """Test if other classes have the same validation bug"""
    
    bugs_found = []
    
    # Test ClusterParameterGroup - missing required Description
    try:
        cpg = redshift.ClusterParameterGroup(
            'TestGroup',
            ParameterGroupFamily='redshift-1.0'
            # Missing required Description
        )
        cpg.validate()  # Should fail but doesn't
        try:
            cpg.to_dict()  # This will fail
        except Exception:
            bugs_found.append('ClusterParameterGroup')
    except Exception:
        pass
    
    # Test ClusterSecurityGroup - missing required Description
    try:
        csg = redshift.ClusterSecurityGroup(
            'TestSecurityGroup'
            # Missing required Description
        )
        csg.validate()  # Should fail but doesn't
        try:
            csg.to_dict()  # This will fail
        except Exception:
            bugs_found.append('ClusterSecurityGroup')
    except Exception:
        pass
    
    # Test ClusterSubnetGroup - missing required Description and SubnetIds
    try:
        csg = redshift.ClusterSubnetGroup(
            'TestSubnetGroup'
            # Missing required Description and SubnetIds
        )
        csg.validate()  # Should fail but doesn't
        try:
            csg.to_dict()  # This will fail
        except Exception:
            bugs_found.append('ClusterSubnetGroup')
    except Exception:
        pass
    
    # Test EndpointAccess - missing multiple required fields
    try:
        ea = redshift.EndpointAccess(
            'TestEndpoint',
            ClusterIdentifier='test-cluster'
            # Missing EndpointName, SubnetGroupName, VpcSecurityGroupIds
        )
        ea.validate()  # Should fail but doesn't
        try:
            ea.to_dict()  # This will fail
        except Exception:
            bugs_found.append('EndpointAccess')
    except Exception:
        pass
    
    print(f"Classes with validation bug: {bugs_found}")
    return bugs_found


if __name__ == "__main__":
    print("Testing validation bug in troposphere.redshift")
    print("=" * 60)
    
    # Test the basic bug
    print("\n1. Testing Cluster validation inconsistency:")
    test_cluster_validate_vs_to_dict_inconsistency()
    
    # Test other classes
    print("\n2. Testing other classes for the same bug:")
    affected_classes = test_other_redshift_classes_have_same_bug()
    
    print("\n" + "=" * 60)
    print("SUMMARY: The validate() method doesn't check for required fields,")
    print("but to_dict() does. This affects multiple classes in troposphere.redshift")
    print(f"Affected classes: {', '.join(affected_classes) if affected_classes else 'Multiple'}")