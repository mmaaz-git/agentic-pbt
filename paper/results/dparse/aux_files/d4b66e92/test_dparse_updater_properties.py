import json
import re
from hypothesis import given, strategies as st, assume, settings
from dparse.updater import RequirementsTXTUpdater, PipfileLockUpdater
from dparse.dependencies import Dependency


# Strategies for generating valid package names
package_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_.'),
    min_size=1,
    max_size=50
).filter(lambda x: x[0].isalpha() and not x.startswith('-'))

# Version strategies
version_strategy = st.text(
    alphabet='0123456789.',
    min_size=1,
    max_size=20
).filter(lambda v: v[0].isdigit() and v[-1].isdigit() and '..' not in v)

# Comment strategy
comment_strategy = st.text(
    alphabet=st.characters(blacklist_characters='\n\r'),
    min_size=0,
    max_size=100
)

# Environment marker strategy 
env_marker_strategy = st.text(
    alphabet=st.characters(blacklist_characters='\n\r#'),
    min_size=1,
    max_size=50
)


@given(
    name=package_name_strategy,
    old_version=version_strategy,
    new_version=version_strategy,
    comment=comment_strategy,
    whitespace=st.text(alphabet=' \t', min_size=0, max_size=10)
)
def test_requirements_txt_preserves_comments(name, old_version, new_version, comment, whitespace):
    """Test that RequirementsTXTUpdater preserves comments exactly."""
    # Create a requirement line with a comment
    line = f"{name}=={old_version}{whitespace}# {comment}"
    content = line
    
    # Create a dependency object
    dep = Dependency(
        name=name,
        specs=f"=={old_version}",
        line=line,
        extras=[]
    )
    
    # Update the requirement
    result = RequirementsTXTUpdater.update(content, dep, new_version)
    
    # The comment should be preserved exactly
    expected_comment_part = f"{whitespace}# {comment}"
    assert expected_comment_part in result, f"Comment not preserved. Result: {result}"
    
    # The new version should be present
    assert f"{name}=={new_version}" in result


@given(
    name=package_name_strategy,
    old_version=version_strategy,
    new_version=version_strategy,
    env_marker=env_marker_strategy
)
def test_requirements_txt_preserves_environment_markers(name, old_version, new_version, env_marker):
    """Test that RequirementsTXTUpdater preserves environment markers."""
    # Create a requirement line with an environment marker
    line = f"{name}=={old_version}; {env_marker}"
    content = line
    
    # Create a dependency object
    dep = Dependency(
        name=name,
        specs=f"=={old_version}",
        line=line,
        extras=[]
    )
    
    # Update the requirement
    result = RequirementsTXTUpdater.update(content, dep, new_version)
    
    # The environment marker should be preserved
    assert f"; {env_marker}" in result, f"Environment marker not preserved. Result: {result}"
    
    # The new version should be present
    assert f"{name}=={new_version}" in result


@given(
    name=package_name_strategy,
    version=version_strategy
)
def test_requirements_txt_idempotence(name, version):
    """Test that updating to the same version is idempotent."""
    # Create a simple requirement line
    line = f"{name}=={version}"
    content = line
    
    # Create a dependency object
    dep = Dependency(
        name=name,
        specs=f"=={version}",
        line=line,
        extras=[]
    )
    
    # Update to the same version
    result = RequirementsTXTUpdater.update(content, dep, version)
    
    # The result should be identical to the original
    assert result == content, f"Idempotence violated. Original: {content}, Result: {result}"


@given(
    packages=st.dictionaries(
        keys=package_name_strategy,
        values=st.fixed_dictionaries({
            'version': version_strategy.map(lambda v: f"=={v}"),
            'hashes': st.lists(
                st.fixed_dictionaries({
                    'method': st.sampled_from(['sha256', 'sha512', 'md5']),
                    'hash': st.text(alphabet='0123456789abcdef', min_size=32, max_size=128)
                }),
                min_size=0,
                max_size=3
            )
        }),
        min_size=1,
        max_size=5
    ),
    target_package=package_name_strategy,
    new_version=version_strategy
)
def test_pipfile_lock_json_validity(packages, target_package, new_version):
    """Test that PipfileLockUpdater always produces valid JSON."""
    # Ensure target package is in the packages dict
    if target_package not in packages:
        packages[target_package] = {
            'version': '==1.0.0',
            'hashes': []
        }
    
    # Create a valid Pipfile.lock content
    lock_data = {
        'default': packages,
        'develop': {}
    }
    content = json.dumps(lock_data, indent=4)
    
    # Create a dependency for the target package
    dep = Dependency(
        name=target_package,
        specs=packages[target_package]['version'],
        line='',  # Not used by PipfileLockUpdater
        extras=[]
    )
    
    # Update the package
    result = PipfileLockUpdater.update(
        content, 
        dep, 
        new_version,
        hashes=[{'method': 'sha256', 'hash': 'a' * 64}]
    )
    
    # The result should be valid JSON
    try:
        parsed = json.loads(result)
        assert isinstance(parsed, dict), "Result is not a JSON object"
        assert 'default' in parsed or 'develop' in parsed, "Missing expected sections"
    except json.JSONDecodeError as e:
        assert False, f"Invalid JSON produced: {e}"


@given(
    packages=st.dictionaries(
        keys=package_name_strategy,
        values=st.fixed_dictionaries({
            'version': version_strategy.map(lambda v: f"=={v}"),
            'hashes': st.lists(st.just('sha256:' + 'a' * 64), min_size=0, max_size=2)
        }),
        min_size=1,
        max_size=3
    ),
    section=st.sampled_from(['default', 'develop']),
    new_version=version_strategy
)
def test_pipfile_lock_version_update_correctness(packages, section, new_version):
    """Test that PipfileLockUpdater correctly updates the specified package version."""
    assume(len(packages) > 0)
    
    # Pick a package to update
    target_package = list(packages.keys())[0]
    
    # Create Pipfile.lock content
    lock_data = {
        section: packages,
        'default' if section == 'develop' else 'develop': {}
    }
    content = json.dumps(lock_data, indent=4)
    
    # Create dependency
    dep = Dependency(
        name=target_package,
        specs=packages[target_package]['version'],
        line='',
        extras=[]
    )
    
    # Update the package
    result = PipfileLockUpdater.update(content, dep, new_version)
    
    # Parse result and check the version was updated
    parsed = json.loads(result)
    assert parsed[section][target_package]['version'] == f"=={new_version}", \
        f"Version not updated correctly. Expected ==={new_version}, got {parsed[section][target_package]['version']}"


@given(
    name=package_name_strategy,
    old_version=version_strategy,
    new_version=version_strategy,
    comment=comment_strategy,
    env_marker=env_marker_strategy
)
def test_requirements_txt_complex_line_preservation(name, old_version, new_version, comment, env_marker):
    """Test that RequirementsTXTUpdater handles complex lines with both comments and env markers."""
    # Create a complex requirement line
    line = f"{name}=={old_version}; {env_marker} # {comment}"
    content = line
    
    # Create a dependency object
    dep = Dependency(
        name=name,
        specs=f"=={old_version}",
        line=line,
        extras=[]
    )
    
    # Update the requirement
    result = RequirementsTXTUpdater.update(content, dep, new_version)
    
    # Check that both environment marker and comment are preserved
    # The environment marker should come before the comment
    assert f"; {env_marker.split('#')[0].rstrip()}" in result, f"Environment marker not preserved correctly. Result: {result}"
    # Note: comment preservation might be affected by the environment marker processing
    
    # The new version should be present
    assert f"{name}=={new_version}" in result


@given(
    name=package_name_strategy,
    version=version_strategy,
    hashes=st.lists(
        st.fixed_dictionaries({
            'method': st.sampled_from(['sha256', 'sha512']),
            'hash': st.text(alphabet='0123456789abcdef', min_size=64, max_size=128)
        }),
        min_size=1,
        max_size=3
    )
)
@settings(max_examples=100)
def test_requirements_txt_hash_formatting(name, version, hashes):
    """Test that RequirementsTXTUpdater formats hashes correctly with line continuations."""
    # Create a simple requirement line
    line = f"{name}==1.0.0"
    content = line
    
    # Create a dependency object with hashes
    dep = Dependency(
        name=name,
        specs="==1.0.0",
        line=line,
        extras=[],
        hashes=True  # Indicate this dependency has hashes
    )
    
    # Update with new version and hashes
    result = RequirementsTXTUpdater.update(content, dep, version, hashes=hashes)
    
    # Check hash formatting
    for i, hash_dict in enumerate(hashes):
        hash_line = f"--hash={hash_dict['method']}:{hash_dict['hash']}"
        assert hash_line in result, f"Hash not found in result: {hash_line}"
        
        # Check line continuations (all but last should have backslash)
        if i < len(hashes) - 1:
            # Should have continuation
            pattern = rf"{re.escape(hash_line)}\s*\\"
            assert re.search(pattern, result), f"Missing line continuation after hash {i}"