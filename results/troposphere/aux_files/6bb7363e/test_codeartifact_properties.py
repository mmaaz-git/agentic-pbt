"""Property-based tests for troposphere.codeartifact module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.codeartifact as codeartifact
import json
import pytest


# Strategy for valid titles (alphanumeric only)
valid_titles = st.text(alphabet=st.characters(min_codepoint=48, max_codepoint=122), min_size=1, max_size=20).filter(lambda s: s.isalnum())

# Strategy for domain names
domain_names = st.text(min_size=1, max_size=50).filter(lambda s: s and not s.isspace())

# Strategy for repository names
repo_names = st.text(min_size=1, max_size=50).filter(lambda s: s and not s.isspace())

# Strategy for descriptions
descriptions = st.text(min_size=0, max_size=200)

# Strategy for patterns
patterns = st.text(min_size=1, max_size=100).filter(lambda s: s and not s.isspace())

# Strategy for restriction modes
restriction_modes = st.sampled_from(["ALLOW", "BLOCK", "ALLOW_SPECIFIC_REPOSITORIES", "INHERIT"])

# Strategy for external connections
external_connections = st.lists(
    st.sampled_from(["public:npmjs", "public:pypi", "public:maven-central", "public:maven-googleandroid"]),
    min_size=0,
    max_size=4,
    unique=True
)

# Strategy for upstream repositories  
upstreams = st.lists(domain_names, min_size=0, max_size=5)


@given(
    title=valid_titles,
    domain_name=domain_names,
    description=descriptions
)
def test_domain_roundtrip(title, domain_name, description):
    """Test that Domain objects can be converted to dict and back"""
    # Create original domain
    original = codeartifact.Domain(
        title=title,
        DomainName=domain_name,
        Tags=[{"Key": "test", "Value": "value"}]
    )
    
    # Convert to dict
    domain_dict = original.to_dict()
    
    # Extract properties
    props = domain_dict["Properties"]
    
    # Create new domain from dict
    reconstructed = codeartifact.Domain.from_dict(title, props)
    
    # They should be equal
    assert original == reconstructed
    assert original.to_json() == reconstructed.to_json()


@given(
    title=valid_titles,
    repo_name=repo_names,
    domain_name=domain_names,
    description=descriptions,
    external_conns=external_connections,
    upstream_repos=upstreams
)
def test_repository_roundtrip(title, repo_name, domain_name, description, external_conns, upstream_repos):
    """Test that Repository objects can be converted to dict and back"""
    # Create original repository
    original = codeartifact.Repository(
        title=title,
        RepositoryName=repo_name,
        DomainName=domain_name,
        Description=description,
        ExternalConnections=external_conns,
        Upstreams=upstream_repos
    )
    
    # Convert to dict
    repo_dict = original.to_dict()
    
    # Extract properties
    props = repo_dict["Properties"]
    
    # Create new repository from dict
    reconstructed = codeartifact.Repository.from_dict(title, props)
    
    # They should be equal
    assert original == reconstructed
    assert original.to_json() == reconstructed.to_json()


@given(
    title1=valid_titles,
    title2=valid_titles, 
    domain_name=domain_names,
    pattern=patterns
)
def test_packagegroup_equality_and_hash(title1, title2, domain_name, pattern):
    """Test that PackageGroup objects with same properties are equal and have same hash"""
    # Create two package groups with same properties
    pg1 = codeartifact.PackageGroup(
        title=title1,
        DomainName=domain_name,
        Pattern=pattern,
        Description="Test description"
    )
    
    pg2 = codeartifact.PackageGroup(
        title=title1,  # Use same title as pg1
        DomainName=domain_name,
        Pattern=pattern,
        Description="Test description"
    )
    
    # If titles are the same, objects should be equal
    if title1 == title2:
        assert pg1 == pg2
        assert hash(pg1) == hash(pg2)
    
    # Create another with different title but same properties
    pg3 = codeartifact.PackageGroup(
        title=title2,
        DomainName=domain_name,
        Pattern=pattern,
        Description="Test description"
    )
    
    # If titles differ, objects should not be equal
    if title1 != title2:
        assert pg1 != pg3
        # Note: hashes might collide but shouldn't be equal in general


@given(
    invalid_title=st.text(min_size=1, max_size=20).filter(lambda s: not s.isalnum()),
    domain_name=domain_names
)
def test_invalid_title_validation(invalid_title, domain_name):
    """Test that non-alphanumeric titles are rejected"""
    assume(not invalid_title.isalnum())  # Ensure it's truly invalid
    
    with pytest.raises(ValueError, match="not alphanumeric"):
        codeartifact.Domain(
            title=invalid_title,
            DomainName=domain_name
        )


@given(
    title=valid_titles,
    mode=restriction_modes,
    repos=st.lists(domain_names, min_size=0, max_size=3)
)
def test_restriction_type_properties(title, mode, repos):
    """Test RestrictionType property class"""
    restriction = codeartifact.RestrictionType(
        RestrictionMode=mode,
        Repositories=repos
    )
    
    # Convert to dict and verify structure
    restriction_dict = restriction.to_dict()
    assert "RestrictionMode" in restriction_dict
    assert restriction_dict["RestrictionMode"] == mode
    if repos:
        assert "Repositories" in restriction_dict
        assert restriction_dict["Repositories"] == repos


@given(title=valid_titles)
def test_domain_required_properties(title):
    """Test that Domain validates required properties"""
    # DomainName is required
    with pytest.raises(ValueError, match="Resource DomainName required"):
        domain = codeartifact.Domain(title=title)
        domain.to_dict()  # Validation happens here


@given(title=valid_titles, domain_name=domain_names)
def test_repository_required_properties(title, domain_name):
    """Test that Repository validates required properties"""
    # RepositoryName is required
    with pytest.raises(ValueError, match="Resource RepositoryName required"):
        repo = codeartifact.Repository(
            title=title,
            DomainName=domain_name
        )
        repo.to_dict()  # Validation happens here


@given(
    title=valid_titles,
    domain_name=domain_names,
    repo_name=repo_names
)  
def test_repository_json_serialization(title, domain_name, repo_name):
    """Test JSON serialization maintains data integrity"""
    repo = codeartifact.Repository(
        title=title,
        RepositoryName=repo_name,
        DomainName=domain_name,
        Description="Test repo"
    )
    
    # Serialize to JSON
    json_str = repo.to_json()
    
    # Parse JSON
    parsed = json.loads(json_str)
    
    # Verify structure
    assert parsed["Type"] == "AWS::CodeArtifact::Repository"
    assert parsed["Properties"]["RepositoryName"] == repo_name
    assert parsed["Properties"]["DomainName"] == domain_name
    assert parsed["Properties"]["Description"] == "Test repo"


@given(
    title=valid_titles,
    domain_name=domain_names,
    pattern=patterns
)
def test_origin_configuration_nesting(title, domain_name, pattern):
    """Test nested property classes work correctly"""
    # Create nested structure
    restriction = codeartifact.RestrictionType(
        RestrictionMode="ALLOW",
        Repositories=["repo1", "repo2"]
    )
    
    restrictions = codeartifact.Restrictions(
        Publish=restriction
    )
    
    origin_config = codeartifact.OriginConfiguration(
        Restrictions=restrictions
    )
    
    # Create PackageGroup with nested config
    pg = codeartifact.PackageGroup(
        title=title,
        DomainName=domain_name,
        Pattern=pattern,
        OriginConfiguration=origin_config
    )
    
    # Convert to dict and verify nested structure
    pg_dict = pg.to_dict()
    assert "Properties" in pg_dict
    assert "OriginConfiguration" in pg_dict["Properties"]
    assert "Restrictions" in pg_dict["Properties"]["OriginConfiguration"]
    assert "Publish" in pg_dict["Properties"]["OriginConfiguration"]["Restrictions"]
    assert pg_dict["Properties"]["OriginConfiguration"]["Restrictions"]["Publish"]["RestrictionMode"] == "ALLOW"


@given(
    title1=valid_titles,
    title2=valid_titles,
    domain_name1=domain_names,
    domain_name2=domain_names
)
@settings(max_examples=50)
def test_domain_inequality(title1, title2, domain_name1, domain_name2):
    """Test that domains with different properties are not equal"""
    d1 = codeartifact.Domain(title=title1, DomainName=domain_name1)
    d2 = codeartifact.Domain(title=title2, DomainName=domain_name2)
    
    # If either title or domain name differs, they should not be equal
    if title1 != title2 or domain_name1 != domain_name2:
        assert d1 != d2
    else:
        assert d1 == d2