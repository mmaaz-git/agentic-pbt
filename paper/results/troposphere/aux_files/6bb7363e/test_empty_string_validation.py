"""Test empty string validation for required string properties"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
import troposphere.codeartifact as codeartifact
from troposphere import Tags

# Test all required string properties with empty strings

def test_domain_empty_string():
    """Test Domain with empty DomainName"""
    domain = codeartifact.Domain(
        title="TestDomain",
        DomainName=""  # Required but accepts empty
    )
    domain_dict = domain.to_dict()
    print(f"Domain with empty DomainName: {domain_dict['Properties']['DomainName']}")
    assert domain_dict["Properties"]["DomainName"] == ""
    

def test_repository_empty_strings():
    """Test Repository with empty required strings"""
    repo = codeartifact.Repository(
        title="TestRepo",
        RepositoryName="",  # Required but accepts empty
        DomainName=""  # Required but accepts empty
    )
    repo_dict = repo.to_dict()
    print(f"Repository with empty RepositoryName: '{repo_dict['Properties']['RepositoryName']}'")
    print(f"Repository with empty DomainName: '{repo_dict['Properties']['DomainName']}'")
    assert repo_dict["Properties"]["RepositoryName"] == ""
    assert repo_dict["Properties"]["DomainName"] == ""


def test_packagegroup_empty_strings():
    """Test PackageGroup with empty required strings"""
    pg = codeartifact.PackageGroup(
        title="TestPG",
        DomainName="",  # Required
        Pattern=""  # Required
    )
    pg_dict = pg.to_dict()
    print(f"PackageGroup with empty DomainName: '{pg_dict['Properties']['DomainName']}'")
    print(f"PackageGroup with empty Pattern: '{pg_dict['Properties']['Pattern']}'")
    assert pg_dict["Properties"]["DomainName"] == ""
    assert pg_dict["Properties"]["Pattern"] == ""


def test_restriction_type_empty_mode():
    """Test RestrictionType with empty RestrictionMode"""
    restriction = codeartifact.RestrictionType(
        RestrictionMode=""  # Required
    )
    restriction_dict = restriction.to_dict()
    print(f"RestrictionType with empty RestrictionMode: '{restriction_dict['RestrictionMode']}'")
    assert restriction_dict["RestrictionMode"] == ""


if __name__ == "__main__":
    print("Testing empty strings for required properties...")
    print("=" * 50)
    
    test_domain_empty_string()
    print()
    
    test_repository_empty_strings()
    print()
    
    test_packagegroup_empty_strings()
    print()
    
    test_restriction_type_empty_mode()
    print()
    
    print("=" * 50)
    print("BUG CONFIRMED: All required string properties accept empty strings!")
    print("This violates the 'required' contract and could cause CloudFormation failures.")