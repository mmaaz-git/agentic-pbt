"""Advanced property-based tests for troposphere.codeartifact to find bugs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import troposphere.codeartifact as codeartifact
from troposphere import Tags
import json
import pytest


# Strategies for edge case testing
edge_case_strings = st.one_of(
    st.just(""),  # Empty string
    st.just(" "),  # Space
    st.just("\n"),  # Newline
    st.just("\t"),  # Tab
    st.text(alphabet=st.characters(whitelist_categories=("Zs", "Cc")), min_size=1, max_size=10),  # Unicode spaces/control
    st.text(min_size=1000, max_size=10000),  # Very long strings
    st.text().filter(lambda x: x.startswith(" ") or x.endswith(" ")),  # Leading/trailing spaces
)

valid_titles = st.text(alphabet=st.characters(min_codepoint=48, max_codepoint=122), min_size=1, max_size=20).filter(lambda s: s.isalnum())

# Test special characters in domain names
special_chars_domain = st.text(alphabet=st.characters(blacklist_categories=("Cc",)), min_size=1, max_size=50)

# Numbers as strings
numeric_strings = st.one_of(
    st.just("0"),
    st.just("123"),
    st.just("-1"),
    st.just("1.5"),
    st.just("1e10"),
)


@given(
    title=valid_titles,
    domain_name=edge_case_strings
)
def test_domain_with_edge_case_names(title, domain_name):
    """Test Domain with edge case domain names"""
    try:
        domain = codeartifact.Domain(
            title=title,
            DomainName=domain_name,
            Tags=Tags({"Test": "Value"})
        )
        # If it accepts the input, verify it roundtrips correctly
        domain_dict = domain.to_dict()
        assert domain_dict["Properties"]["DomainName"] == domain_name
    except (ValueError, TypeError) as e:
        # The library might reject some edge cases, which is fine
        pass


@given(
    title=valid_titles,
    external_connections=st.lists(
        st.text(min_size=1, max_size=100),
        min_size=0,
        max_size=10
    )
)
def test_repository_external_connections_validation(title, external_connections):
    """Test Repository with various external connection formats"""
    try:
        repo = codeartifact.Repository(
            title=title,
            RepositoryName="test-repo",
            DomainName="test-domain",
            ExternalConnections=external_connections
        )
        repo_dict = repo.to_dict()
        if external_connections:
            assert repo_dict["Properties"]["ExternalConnections"] == external_connections
    except (ValueError, TypeError):
        # Some formats might be rejected
        pass


@given(
    title=valid_titles,
    pattern=st.text(min_size=0, max_size=200)
)
def test_packagegroup_pattern_edge_cases(title, pattern):
    """Test PackageGroup with various pattern formats including empty"""
    if pattern == "":
        # Empty pattern should fail since it's required
        with pytest.raises(ValueError):
            pg = codeartifact.PackageGroup(
                title=title,
                DomainName="test-domain",
                Pattern=pattern
            )
            pg.to_dict()
    else:
        pg = codeartifact.PackageGroup(
            title=title,
            DomainName="test-domain",
            Pattern=pattern
        )
        pg_dict = pg.to_dict()
        assert pg_dict["Properties"]["Pattern"] == pattern


@given(
    title=valid_titles,
    wrong_type_value=st.one_of(
        st.integers(),
        st.floats(),
        st.booleans(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    )
)
def test_domain_wrong_type_for_string_property(title, wrong_type_value):
    """Test that non-string values for DomainName are rejected"""
    if isinstance(wrong_type_value, str):
        return  # Skip strings
    
    with pytest.raises(TypeError):
        domain = codeartifact.Domain(
            title=title,
            DomainName=wrong_type_value
        )


@given(
    title=valid_titles,
    repos=st.one_of(
        st.just(None),
        st.text(),  # Should be a list
        st.integers(),
        st.dictionaries(st.text(), st.text())
    )
)
def test_restriction_type_wrong_repos_type(title, repos):
    """Test RestrictionType with wrong type for Repositories"""
    if isinstance(repos, list) or repos is None:
        return  # Skip valid types
    
    with pytest.raises(TypeError):
        restriction = codeartifact.RestrictionType(
            RestrictionMode="ALLOW",
            Repositories=repos
        )


@given(
    title=valid_titles,
    mode=st.text(min_size=1, max_size=50)
)
def test_restriction_mode_accepts_any_string(title, mode):
    """Test if RestrictionMode validates against allowed values"""
    # RestrictionMode should probably only accept specific values
    # but let's test if it validates
    restriction = codeartifact.RestrictionType(
        RestrictionMode=mode
    )
    restriction_dict = restriction.to_dict()
    assert restriction_dict["RestrictionMode"] == mode
    # This might reveal that any string is accepted when only specific modes should be


@given(
    title1=valid_titles,
    title2=valid_titles
)
def test_object_mutation_after_creation(title1, title2):
    """Test if objects can be mutated after creation"""
    domain = codeartifact.Domain(
        title=title1,
        DomainName="original-domain"
    )
    
    # Try to change the domain name
    domain.DomainName = "modified-domain"
    
    # Check if the change persists
    domain_dict = domain.to_dict()
    assert domain_dict["Properties"]["DomainName"] == "modified-domain"
    
    # Also test that title changes work
    original_title = domain.title
    domain.title = title2
    assert domain.title == title2


@given(
    title=valid_titles,
    domain_owner=st.one_of(
        st.just(""),
        st.just("123456789012"),  # Valid AWS account ID
        st.just("not-a-number"),
        st.text(alphabet="0123456789", min_size=1, max_size=20)
    )
)
def test_domain_owner_validation(title, domain_owner):
    """Test if DomainOwner (AWS account ID) is validated"""
    repo = codeartifact.Repository(
        title=title,
        RepositoryName="test-repo",
        DomainName="test-domain",
        DomainOwner=domain_owner
    )
    repo_dict = repo.to_dict()
    if domain_owner:
        assert repo_dict["Properties"]["DomainOwner"] == domain_owner


@given(
    title=valid_titles,
    contact_info=st.text(min_size=0, max_size=1000)
)
def test_packagegroup_contact_info_length(title, contact_info):
    """Test PackageGroup ContactInfo with various lengths"""
    pg = codeartifact.PackageGroup(
        title=title,
        DomainName="test-domain",
        Pattern="com.example.*",
        ContactInfo=contact_info
    )
    pg_dict = pg.to_dict()
    if contact_info:
        assert pg_dict["Properties"]["ContactInfo"] == contact_info


@given(
    title=valid_titles,
    key=st.text(min_size=0, max_size=200),
    value=st.text(min_size=0, max_size=200)
)
def test_tags_with_empty_keys_or_values(title, key, value):
    """Test if Tags accept empty keys or values"""
    try:
        domain = codeartifact.Domain(
            title=title,
            DomainName="test-domain",
            Tags=Tags({key: value})
        )
        domain_dict = domain.to_dict()
        # Check if empty key/value tags are preserved
        if "Tags" in domain_dict["Properties"]:
            tags = domain_dict["Properties"]["Tags"]
            if isinstance(tags, list) and len(tags) > 0:
                assert any(t.get("Key") == key for t in tags)
    except (ValueError, TypeError, KeyError):
        # Empty keys might be rejected
        pass


@given(title=valid_titles)
def test_repository_with_circular_upstream_reference(title):
    """Test if Repository allows self-reference in Upstreams"""
    repo = codeartifact.Repository(
        title=title,
        RepositoryName="self-referencing-repo",
        DomainName="test-domain",
        Upstreams=["self-referencing-repo"]  # Points to itself
    )
    # This should probably be validated but let's see if it's accepted
    repo_dict = repo.to_dict()
    assert repo_dict["Properties"]["Upstreams"] == ["self-referencing-repo"]


@given(
    title=valid_titles,
    dict_data=st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.text(min_size=1, max_size=50),
        min_size=1,
        max_size=5
    )
)
def test_from_dict_with_extra_properties(title, dict_data):
    """Test from_dict with properties not in the schema"""
    # Add required properties
    dict_data["DomainName"] = "test-domain"
    
    # Add some extra properties that shouldn't exist
    dict_data["NonExistentProperty"] = "value"
    dict_data["AnotherFakeProperty"] = 123
    
    # This should raise an error for unknown properties
    with pytest.raises(AttributeError):
        domain = codeartifact.Domain.from_dict(title, dict_data)