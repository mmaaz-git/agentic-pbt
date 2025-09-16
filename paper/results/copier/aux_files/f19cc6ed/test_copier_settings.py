"""Property-based tests for copier.settings module."""

import os
import tempfile
from pathlib import Path

import yaml
from hypothesis import assume, given, strategies as st

# Ensure we use the copier from the virtual environment
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from copier.settings import Settings


# Strategies for generating test data
valid_url_chars = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~:/?#[]@!$&'()*+,;=", min_size=1)
trusted_repo_strategy = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._:/", min_size=1, max_size=100)
path_segment = st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._", min_size=1, max_size=20)


@given(
    trusted_repos=st.sets(trusted_repo_strategy, min_size=1, max_size=10),
    test_repo=trusted_repo_strategy
)
def test_is_trusted_prefix_matching(trusted_repos, test_repo):
    """Test that prefix matching works correctly for trusted repositories."""
    # Add some repos with "/" suffix for prefix matching
    trust_set = set()
    for repo in trusted_repos:
        if not repo.endswith("/"):
            # Randomly make some prefix matchers
            if len(repo) % 2 == 0:
                trust_set.add(repo + "/")
            else:
                trust_set.add(repo)
        else:
            trust_set.add(repo)
    
    settings = Settings(trust=trust_set)
    
    # Property: If a repo starts with a trusted prefix (ending with /), it should be trusted
    for trusted in trust_set:
        if trusted.endswith("/"):
            # Any repo starting with this prefix should be trusted
            if test_repo.startswith(trusted[:-1]):
                assert settings.is_trusted(test_repo), f"{test_repo} should be trusted as it starts with {trusted}"
        else:
            # Only exact match should be trusted
            if test_repo == trusted:
                assert settings.is_trusted(test_repo), f"{test_repo} should be trusted as it exactly matches {trusted}"


@given(url=st.text(min_size=0, max_size=200))
def test_normalize_idempotence(url):
    """Test that normalize is idempotent."""
    settings = Settings()
    
    # Skip URLs that would cause OS errors
    assume(not any(c in url for c in '\x00'))
    
    # Property: normalize(normalize(x)) == normalize(x)
    normalized_once = settings.normalize(url)
    normalized_twice = settings.normalize(normalized_once)
    
    assert normalized_once == normalized_twice, f"normalize not idempotent for {url!r}"


@given(url=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._/", min_size=1))
def test_normalize_tilde_expansion(url):
    """Test that ~ expansion works correctly and consistently."""
    settings = Settings()
    
    # Test with tilde at the beginning
    if url.startswith("~"):
        normalized = settings.normalize(url)
        # It should expand the tilde
        assert not normalized.startswith("~"), f"Tilde not expanded in {url}"
        # Should be idempotent after expansion
        assert settings.normalize(normalized) == normalized
    else:
        # Non-tilde URLs should remain unchanged
        assert settings.normalize(url) == url


@given(
    defaults_data=st.dictionaries(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=20),
        st.one_of(st.text(max_size=100), st.integers(), st.booleans(), st.none()),
        max_size=10
    ),
    trust_data=st.sets(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._:/", min_size=1, max_size=50),
        max_size=10
    )
)
def test_settings_yaml_round_trip(defaults_data, trust_data):
    """Test that Settings can be saved to YAML and loaded back consistently."""
    # Create a Settings instance
    original = Settings(defaults=defaults_data, trust=trust_data)
    
    # Save to temporary YAML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(original.model_dump(), f)
        temp_path = Path(f.name)
    
    try:
        # Load from the YAML file
        loaded = Settings.from_file(temp_path)
        
        # Property: Round-trip should preserve data
        assert loaded.defaults == original.defaults, "Defaults not preserved in round-trip"
        assert loaded.trust == original.trust, "Trust not preserved in round-trip"
    finally:
        temp_path.unlink()


@given(
    repo=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._:/", min_size=1, max_size=100),
    prefix_len=st.integers(min_value=1, max_value=50)
)
def test_is_trusted_substring_consistency(repo, prefix_len):
    """Test that prefix trust relationships are consistent."""
    assume(prefix_len < len(repo))
    
    prefix = repo[:prefix_len]
    
    # If we trust a prefix, we should trust anything starting with it
    settings_with_prefix = Settings(trust={prefix + "/"})
    settings_with_exact = Settings(trust={prefix})
    
    # Property: prefix trust should trust the full repo if it starts with prefix
    if repo.startswith(prefix):
        assert settings_with_prefix.is_trusted(repo), f"Prefix trust {prefix}/ should trust {repo}"
    
    # Property: exact trust should only trust exact matches
    if repo == prefix:
        assert settings_with_exact.is_trusted(repo), f"Exact trust {prefix} should trust exact match"
    else:
        assert not settings_with_exact.is_trusted(repo), f"Exact trust {prefix} should not trust {repo}"


@given(
    base_url=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._", min_size=1, max_size=30),
    suffixes=st.lists(st.text(alphabet="/abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10), min_size=0, max_size=5)
)
def test_is_trusted_normalization_consistency(base_url, suffixes):
    """Test that is_trusted works correctly with normalized URLs."""
    # Build a URL with potential tilde
    url = "~/" + base_url + "".join(suffixes)
    
    settings = Settings(trust={url})
    
    # The repository checking should handle normalization internally
    # Property: A URL should match its normalized form
    normalized = settings.normalize(url)
    
    # If we trust the original URL, we should trust its normalized form when checked
    if settings.is_trusted(url):
        # The is_trusted method should normalize internally
        assert url in settings.trust or url + "/" in settings.trust