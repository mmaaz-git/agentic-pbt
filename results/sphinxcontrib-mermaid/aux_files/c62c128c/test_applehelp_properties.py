#!/usr/bin/env python3
"""Property-based tests for sphinxcontrib.applehelp using Hypothesis."""

import sys
import os
import tempfile
import plistlib
from pathlib import Path
from io import BytesIO

sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from sphinx.util.osutil import make_filename
import shlex

# Property 1: make_filename should create valid filenames and have consistent behavior
@given(st.text())
def test_make_filename_consistency(project_name):
    """Test that make_filename creates consistent and valid filenames."""
    result = make_filename(project_name)
    
    # Property: Result should always be a string
    assert isinstance(result, str)
    
    # Property: Result should not be empty (fallback to 'sphinx')
    assert len(result) > 0
    
    # Property: Result should not contain problematic filename characters
    # Based on the regex pattern in the source, it removes non-alphanumeric chars
    for char in result:
        assert char.isalnum() or char in '-_', f"Invalid character '{char}' in filename"
    
    # Property: Empty or non-alphanumeric strings should return 'sphinx'
    if not any(c.isalnum() for c in project_name):
        assert result == 'sphinx'
    
    # Property: Idempotence - applying make_filename twice should give same result
    assert make_filename(result) == result


# Property 2: Info.plist round-trip through plistlib
@given(
    st.text(min_size=1),  # bundle_id
    st.text(min_size=1),  # dev_region
    st.text(min_size=1),  # release
    st.text(min_size=1),  # bundle_version
    st.text(min_size=1),  # title
    st.one_of(st.none(), st.text(min_size=1)),  # icon
    st.one_of(st.none(), st.text(min_size=1)),  # kb_product
    st.one_of(st.none(), st.text(min_size=1)),  # kb_url
    st.one_of(st.none(), st.text(min_size=1)),  # remote_url
)
def test_plist_round_trip(bundle_id, dev_region, release, bundle_version, title, 
                          icon, kb_product, kb_url, remote_url):
    """Test that Info.plist data can round-trip through plistlib."""
    
    # Create the info_plist dict as done in build_info_plist
    info_plist = {
        'CFBundleDevelopmentRegion': dev_region,
        'CFBundleIdentifier': bundle_id,
        'CFBundleInfoDictionaryVersion': '6.0',
        'CFBundlePackageType': 'BNDL',
        'CFBundleShortVersionString': release,
        'CFBundleSignature': 'hbwr',
        'CFBundleVersion': bundle_version,
        'HPDBookAccessPath': '_access.html',
        'HPDBookIndexPath': 'search.helpindex',
        'HPDBookTitle': title,
        'HPDBookType': '3',
        'HPDBookUsesExternalViewer': False,
    }
    
    if icon is not None:
        info_plist['HPDBookIconPath'] = os.path.basename(icon)
    
    if kb_url is not None:
        info_plist['HPDBookKBProduct'] = kb_product or ''
        info_plist['HPDBookKBURL'] = kb_url
    
    if remote_url is not None:
        info_plist['HPDBookRemoteURL'] = remote_url
    
    # Test round-trip
    buffer = BytesIO()
    plistlib.dump(info_plist, buffer)
    buffer.seek(0)
    loaded = plistlib.load(buffer)
    
    # Property: Data should be preserved exactly
    assert loaded == info_plist
    
    # Property: All required keys should be present
    required_keys = [
        'CFBundleDevelopmentRegion', 'CFBundleIdentifier', 
        'CFBundleInfoDictionaryVersion', 'CFBundlePackageType',
        'CFBundleShortVersionString', 'CFBundleSignature',
        'CFBundleVersion', 'HPDBookAccessPath', 'HPDBookIndexPath',
        'HPDBookTitle', 'HPDBookType', 'HPDBookUsesExternalViewer'
    ]
    for key in required_keys:
        assert key in loaded


# Property 3: shlex.quote should properly escape shell arguments
@given(st.text())
def test_shlex_quote_safety(arg):
    """Test that shlex.quote properly escapes shell arguments."""
    quoted = shlex.quote(arg)
    
    # Property: Quoted string should be a string
    assert isinstance(quoted, str)
    
    # Property: If arg contains special chars, it should be quoted
    special_chars = ' \t\n\r|&;<>()$`\\"\'*?[#~=%'
    if any(c in arg for c in special_chars):
        # Should either be wrapped in single quotes or have escaping
        assert (quoted.startswith("'") and quoted.endswith("'")) or '\\' in quoted
    
    # Property: Empty string should be quoted
    if arg == '':
        assert quoted == "''"
    
    # Property: Alphanumeric-only strings might not need quoting
    if arg and all(c.isalnum() or c in '-_./=' for c in arg):
        # These are generally safe and might not be quoted
        pass  # No specific assertion as shlex.quote may or may not quote these


# Property 4: Bundle path structure
@given(
    st.text(min_size=1, alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters='/')),
    st.text(min_size=1, alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters='/'))
)
def test_bundle_path_structure(bundle_name, locale):
    """Test that bundle path structure is created correctly."""
    assume(bundle_name)  # Non-empty
    assume(locale)  # Non-empty
    
    # Simulate the path construction from the init method
    outdir = '/tmp/test_output'
    bundle_path = os.path.join(outdir, bundle_name + '.help')
    final_outdir = Path(
        bundle_path,
        'Contents',
        'Resources',
        locale + '.lproj',
    )
    
    # Property: Path should be absolute
    assert final_outdir.is_absolute()
    
    # Property: Path should contain expected components
    path_str = str(final_outdir)
    assert '.help' in path_str
    assert 'Contents' in path_str
    assert 'Resources' in path_str
    assert '.lproj' in path_str
    
    # Property: Path components should be in correct order
    parts = final_outdir.parts
    help_idx = next(i for i, p in enumerate(parts) if p.endswith('.help'))
    contents_idx = next(i for i, p in enumerate(parts) if p == 'Contents')
    resources_idx = next(i for i, p in enumerate(parts) if p == 'Resources')
    lproj_idx = next(i for i, p in enumerate(parts) if p.endswith('.lproj'))
    
    assert help_idx < contents_idx < resources_idx < lproj_idx


# Property 5: Path join consistency between os.path and pathlib
@given(
    st.lists(st.text(min_size=1, alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters='/')), min_size=2, max_size=5)
)
def test_path_join_consistency(path_components):
    """Test that os.path.join and pathlib.Path give consistent results."""
    assume(all(comp for comp in path_components))  # All non-empty
    
    # Using os.path.join
    os_path_result = os.path.join(*path_components)
    
    # Using pathlib.Path
    pathlib_result = str(Path(*path_components))
    
    # Property: Both should normalize to the same path
    # Note: They might differ in exact representation but should be equivalent
    assert Path(os_path_result) == Path(pathlib_result)


if __name__ == '__main__':
    # Run a quick test to ensure imports work
    print("Testing sphinxcontrib.applehelp properties...")
    test_make_filename_consistency()
    test_plist_round_trip()
    test_shlex_quote_safety()
    test_bundle_path_structure()
    test_path_join_consistency()
    print("Basic tests passed!")